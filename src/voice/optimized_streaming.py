import asyncio
import discord
import numpy as np
import torch
import whisper
from TTS.api import TTS
from transformers import AutoTokenizer, AutoModelForCausalLM
import io
import wave
from typing import AsyncGenerator, Optional, Dict
import logging
import re
from collections import deque
from ..utils.concurrency import concurrency_manager
from ..models.llm_fallback import llm_fallback
from ..core.personality import personality_system
from ..memory.persistent_memory import memory_system
from ..utils.logging import get_logger

logger = get_logger(__name__)

class StreamingLLM:
    def __init__(self):
        self.tokenizer = None
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
    
    async def load_model(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
    
    def _load_model_sync(self):
        self.tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        self.model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium").to(self.device)
        self.tokenizer.pad_token = self.tokenizer.eos_token
    
    async def stream_response(self, prompt: str) -> AsyncGenerator[str, None]:
        inputs = self.tokenizer.encode(prompt + self.tokenizer.eos_token, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            for _ in range(100):
                outputs = self.model(inputs)
                next_token_logits = outputs.logits[0, -1, :]
                next_token = torch.multinomial(torch.softmax(next_token_logits, dim=-1), num_samples=1)
                
                if next_token.item() == self.tokenizer.eos_token_id:
                    break
                
                inputs = torch.cat([inputs, next_token.unsqueeze(0)], dim=-1)
                token_text = self.tokenizer.decode(next_token, skip_special_tokens=True)
                
                if token_text.strip():
                    yield token_text
                
                await asyncio.sleep(0)

class SentenceChunker:
    def __init__(self):
        self.buffer = ""
        self.sentence_endings = re.compile(r'[.!?]+\s*')
    
    def add_token(self, token: str) -> Optional[str]:
        self.buffer += token
        
        match = self.sentence_endings.search(self.buffer)
        if match:
            sentence = self.buffer[:match.end()].strip()
            self.buffer = self.buffer[match.end():]
            return sentence
        
        if len(self.buffer) > 200:
            sentence = self.buffer[:200].strip()
            self.buffer = self.buffer[200:]
            return sentence
        
        return None
    
    def flush(self) -> Optional[str]:
        if self.buffer.strip():
            sentence = self.buffer.strip()
            self.buffer = ""
            return sentence
        return None

class AsyncTTS:
    def __init__(self):
        self.tts = None
        self.sample_rate = 22050
    
    async def load_model(self):
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._load_model_sync)
    
    def _load_model_sync(self):
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
        self.tts.to("cuda" if torch.cuda.is_available() else "cpu")
    
    async def synthesize(self, text: str) -> bytes:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._synthesize_sync, text)
    
    def _synthesize_sync(self, text: str) -> bytes:
        # Add emotion and prosody based on text content
        emotion = self._detect_emotion(text)
        
        # Configure TTS with emotion
        wav = self.tts.tts(
            text=text,
            emotion=emotion,
            speed=1.1 if "!" in text else 0.95,
            pitch_shift=0.1 if "?" in text else 0.0
        )
        
        wav_np = np.array(wav, dtype=np.float32)
        wav_int16 = (wav_np * 32767).astype(np.int16)
        
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(wav_int16.tobytes())
        
        return buffer.getvalue()
    
    def _detect_emotion(self, text: str) -> str:
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["excited", "amazing", "awesome", "yay", "woohoo"]):
            return "excited"
        elif any(word in text_lower for word in ["sad", "sorry", "disappointed", "upset"]):
            return "sad"
        elif "?" in text:
            return "curious"
        elif "!" in text:
            return "enthusiastic"
        elif any(word in text_lower for word in ["angry", "mad", "frustrated", "annoyed"]):
            return "angry"
        else:
            return "neutral"

class AsyncAudioSource(discord.AudioSource):
    def __init__(self):
        self.audio_queue = asyncio.Queue()
        self.current_audio = None
        self.position = 0
        self.finished = False
    
    async def add_audio(self, audio_data: bytes):
        await self.audio_queue.put(audio_data)
    
    def read(self) -> bytes:
        if self.finished:
            return b''
        
        try:
            if not self.current_audio or self.position >= len(self.current_audio):
                try:
                    self.current_audio = self.audio_queue.get_nowait()
                    self.position = 0
                except asyncio.QueueEmpty:
                    return b'\x00' * 3840
            
            chunk_size = 3840
            chunk = self.current_audio[self.position:self.position + chunk_size]
            self.position += len(chunk)
            
            if len(chunk) < chunk_size:
                chunk += b'\x00' * (chunk_size - len(chunk))
            
            return chunk
            
        except Exception as e:
            logger.error(f"Audio read error: {e}")
            return b'\x00' * 3840
    
    def is_opus(self) -> bool:
        return False
    
    def cleanup(self):
        self.finished = True

class StreamingVoice:
    def __init__(self):
        self.streaming_llm = StreamingLLM()
        self.tts = AsyncTTS()
        self.whisper_model = None
        self.voice_clients: Dict[str, discord.VoiceClient] = {}
        self.audio_buffers: Dict[str, deque] = {}
        self.is_processing: Dict[str, bool] = {}
        
    async def initialize(self):
        tasks = [
            self._load_whisper(),
            self.streaming_llm.load_model(),
            self.tts.load_model()
        ]
        await asyncio.gather(*tasks)
        logger.info("Streaming voice initialized")
    
    async def _load_whisper(self):
        loop = asyncio.get_event_loop()
        self.whisper_model = await loop.run_in_executor(None, whisper.load_model, "base")
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._transcribe_sync, audio_data)
    
    def _transcribe_sync(self, audio_data: bytes) -> str:
        audio_np = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        result = self.whisper_model.transcribe(audio_np)
        return result["text"].strip()
    
    async def process_voice_input(self, user_id: str, audio_data: bytes, voice_client: discord.VoiceClient):
        if self.is_processing.get(user_id, False):
            return
        
        self.is_processing[user_id] = True
        try:
            text = await self.transcribe_audio(audio_data)
            if not text:
                return
            
            logger.info(f"Transcribed from {user_id}: {text}")
            
            chunker = SentenceChunker()
            audio_source = AsyncAudioSource()
            
            voice_client.play(audio_source)
            
            async for token in self.streaming_llm.stream_response(text):
                sentence = chunker.add_token(token)
                if sentence:
                    asyncio.create_task(self._process_sentence(sentence, audio_source))
            
            final_sentence = chunker.flush()
            if final_sentence:
                asyncio.create_task(self._process_sentence(final_sentence, audio_source))
            
        finally:
            self.is_processing[user_id] = False
    
    async def _process_sentence(self, sentence: str, audio_source: AsyncAudioSource):
        try:
            audio_data = await self.tts.synthesize(sentence)
            await audio_source.add_audio(audio_data)
        except Exception as e:
            logger.error(f"TTS error: {e}")
    
    async def join_voice_channel(self, channel: discord.VoiceChannel, user_id: str) -> discord.VoiceClient:
        voice_client = await channel.connect()
        self.voice_clients[str(channel.guild.id)] = voice_client
        self.audio_buffers[str(channel.guild.id)] = deque(maxlen=1000)
        
        voice_client.start_recording(
            discord.sinks.WaveSink(),
            self._audio_callback,
            channel.guild.id
        )
        
        return voice_client
    
    async def _audio_callback(self, sink: discord.sinks.WaveSink, guild_id: int):
        for user_id, audio in sink.audio_data.items():
            if user_id == self.voice_clients[str(guild_id)].user.id:
                continue
            
            audio_data = audio.file.getvalue()
            if len(audio_data) > 1000:
                voice_client = self.voice_clients.get(str(guild_id))
                if voice_client:
                    asyncio.create_task(
                        self.process_voice_input(str(user_id), audio_data, voice_client)
                    )
    
    async def leave_voice_channel(self, guild_id: str):
        voice_client = self.voice_clients.get(guild_id)
        if voice_client:
            voice_client.stop_recording()
            await voice_client.disconnect()
            del self.voice_clients[guild_id]
            if guild_id in self.audio_buffers:
                del self.audio_buffers[guild_id]
    
    async def start_listening(self, user_id: str):
        pass
    
    async def stop_listening(self, user_id: str):
        pass
    
    async def cleanup(self):
        for guild_id in list(self.voice_clients.keys()):
            await self.leave_voice_channel(guild_id)

streaming_voice = StreamingVoice()