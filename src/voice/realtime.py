"""Real-time voice processing with VAD and streaming for seamless conversation."""
import asyncio
import aiohttp
import tempfile
import time
import os
from typing import Dict, Optional, Callable, Any
from pathlib import Path
import threading
import queue
from ..config.settings import config
from ..utils.logging import logger

# Voice Activity Detection
try:
    import webrtcvad
    import pyaudio
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logger.warning("webrtcvad/pyaudio not available - limited voice features")

class RealTimeVoice:
    """Real-time voice processing with <800ms total latency."""
    
    def __init__(self):
        self.session = None
        self.vad = None
        self.is_listening = False
        self.is_speaking = False
        self.audio_queue = queue.Queue()
        self.transcript_callback = None
        self.response_callback = None
        
        # Audio settings optimized for speed
        self.sample_rate = 16000
        self.chunk_size = 320  # 20ms chunks
        self.channels = 1
        
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(2)  # Aggressiveness level
            
    async def start_session(self):
        """Initialize HTTP session for API calls."""
        if not self.session:
            timeout = aiohttp.ClientTimeout(total=2, connect=0.5)
            connector = aiohttp.TCPConnector(limit=10, keepalive_timeout=30)
            self.session = aiohttp.ClientSession(timeout=timeout, connector=connector)
    
    def start_listening(self, transcript_callback: Callable, response_callback: Callable):
        """Start real-time voice listening with callbacks."""
        if not VAD_AVAILABLE:
            logger.error("Voice features not available - install webrtcvad and pyaudio")
            return False
            
        self.transcript_callback = transcript_callback
        self.response_callback = response_callback
        self.is_listening = True
        
        # Start audio capture thread
        threading.Thread(target=self._audio_capture_thread, daemon=True).start()
        
        # Start processing thread
        threading.Thread(target=self._audio_process_thread, daemon=True).start()
        
        logger.info("Real-time voice listening started")
        return True
    
    def _audio_capture_thread(self):
        """Capture audio in real-time."""
        try:
            audio = pyaudio.PyAudio()
            stream = audio.open(
                format=pyaudio.paInt16,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size
            )
            
            logger.info("Audio capture started")
            
            while self.is_listening:
                try:
                    data = stream.read(self.chunk_size, exception_on_overflow=False)
                    self.audio_queue.put(data)
                except Exception as e:
                    logger.error(f"Audio capture error: {e}")
                    break
            
            stream.stop_stream()
            stream.close()
            audio.terminate()
            
        except Exception as e:
            logger.error(f"Audio capture thread failed: {e}")
    
    def _audio_process_thread(self):
        """Process audio chunks for voice activity."""
        speech_frames = []
        silence_count = 0
        speech_detected = False
        
        while self.is_listening:
            try:
                # Get audio chunk with timeout
                try:
                    audio_chunk = self.audio_queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                
                # Voice Activity Detection
                is_speech = self._detect_speech(audio_chunk)
                
                if is_speech:
                    speech_frames.append(audio_chunk)
                    silence_count = 0
                    
                    if not speech_detected:
                        speech_detected = True
                        logger.debug("Speech started")
                        
                else:
                    silence_count += 1
                    
                    # End of speech detection (500ms of silence)
                    if speech_detected and silence_count > 25:  # 25 * 20ms = 500ms
                        if speech_frames:
                            logger.debug("Speech ended, processing...")
                            asyncio.create_task(self._process_speech(speech_frames.copy()))
                        
                        speech_frames.clear()
                        speech_detected = False
                        silence_count = 0
                
            except Exception as e:
                logger.error(f"Audio processing error: {e}")
    
    def _detect_speech(self, audio_chunk: bytes) -> bool:
        """Detect if audio chunk contains speech."""
        if not self.vad:
            return True
        
        try:
            return self.vad.is_speech(audio_chunk, self.sample_rate)
        except:
            return True
    
    async def _process_speech(self, speech_frames: list):
        """Process detected speech end-to-end."""
        start_time = time.time()
        
        try:
            # Convert frames to audio file
            audio_data = b''.join(speech_frames)
            temp_file = tempfile.mktemp(suffix='.wav')
            
            self._save_wav(audio_data, temp_file)
            
            # Step 1: Fast transcription
            transcript = await self._fast_transcribe(temp_file)
            transcript_time = time.time() - start_time
            
            if not transcript:
                return
            
            logger.info(f"Transcribed in {transcript_time*1000:.0f}ms: {transcript}")
            
            # Callback for transcript
            if self.transcript_callback:
                await self.transcript_callback(transcript)
            
            # Step 2: Generate response
            response_start = time.time()
            if self.response_callback:
                response_text = await self.response_callback(transcript)
                response_time = time.time() - response_start
                
                if response_text:
                    logger.info(f"Generated response in {response_time*1000:.0f}ms")
                    
                    # Step 3: Speak response
                    await self._fast_speak(response_text)
                    
                    total_time = time.time() - start_time
                    logger.info(f"Total voice pipeline: {total_time*1000:.0f}ms")
            
            # Cleanup
            try:
                os.unlink(temp_file)
            except:
                pass
                
        except Exception as e:
            logger.error(f"Speech processing failed: {e}")
    
    def _save_wav(self, audio_data: bytes, filename: str):
        """Save audio data as WAV file."""
        import wave
        
        with wave.open(filename, 'wb') as wav_file:
            wav_file.setnchannels(self.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(audio_data)
    
    async def _fast_transcribe(self, audio_file: str) -> str:
        """Ultra-fast transcription with parallel providers."""
        await self.start_session()
        
        # Race Groq and local Whisper
        tasks = []
        
        # Groq Whisper (fastest)
        if config.has_api_key('groq'):
            tasks.append(asyncio.create_task(self._groq_transcribe(audio_file)))
        
        # Local Whisper fallback
        tasks.append(asyncio.create_task(self._local_transcribe(audio_file)))
        
        if not tasks:
            return ""
        
        try:
            done, pending = await asyncio.wait(
                tasks, return_when=asyncio.FIRST_COMPLETED, timeout=1.5
            )
            
            for task in pending:
                task.cancel()
            
            for task in done:
                try:
                    result = await task
                    if result:
                        return result
                except:
                    continue
                    
        except asyncio.TimeoutError:
            logger.warning("Transcription timeout")
        
        return ""
    
    async def _groq_transcribe(self, audio_file: str) -> str:
        """Groq Whisper transcription."""
        try:
            with open(audio_file, 'rb') as f:
                data = aiohttp.FormData()
                data.add_field('file', f, filename='audio.wav')
                data.add_field('model', 'whisper-1')
                
                async with self.session.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    headers={'Authorization': f'Bearer {config.get_api_key("groq")}'},
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return result.get('text', '').strip()
        except Exception as e:
            logger.warning(f"Groq transcription failed: {e}")
        
        return ""
    
    async def _local_transcribe(self, audio_file: str) -> str:
        """Local Whisper transcription."""
        try:
            from faster_whisper import WhisperModel
            
            if not hasattr(self, '_whisper_model'):
                self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            
            loop = asyncio.get_event_loop()
            
            def transcribe():
                segments, _ = self._whisper_model.transcribe(audio_file)
                return " ".join([seg.text for seg in segments]).strip()
            
            return await loop.run_in_executor(None, transcribe)
            
        except Exception as e:
            logger.warning(f"Local transcription failed: {e}")
        
        return ""
    
    async def _fast_speak(self, text: str):
        """Ultra-fast text-to-speech."""
        try:
            # Race ElevenLabs and Edge TTS
            tasks = []
            
            if config.has_api_key('elevenlabs'):
                tasks.append(asyncio.create_task(self._elevenlabs_speak(text)))
            
            tasks.append(asyncio.create_task(self._edge_speak(text)))
            
            if tasks:
                done, pending = await asyncio.wait(
                    tasks, return_when=asyncio.FIRST_COMPLETED, timeout=2
                )
                
                for task in pending:
                    task.cancel()
                
                for task in done:
                    try:
                        audio_file = await task
                        if audio_file and os.path.exists(audio_file):
                            await self._play_audio(audio_file)
                            return
                    except:
                        continue
        
        except Exception as e:
            logger.error(f"Speech synthesis failed: {e}")
    
    async def _elevenlabs_speak(self, text: str) -> str:
        """ElevenLabs TTS."""
        try:
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {
                    "stability": 0.7,
                    "similarity_boost": 0.8,
                    "style": 0.2
                }
            }
            
            voice_id = "21m00Tcm4TlvDq8ikWAM"
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
            
            async with self.session.post(
                url,
                headers={'xi-api-key': config.get_api_key('elevenlabs')},
                json=payload
            ) as response:
                if response.status == 200:
                    temp_file = tempfile.mktemp(suffix='.mp3')
                    with open(temp_file, 'wb') as f:
                        f.write(await response.read())
                    return temp_file
        
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")
        
        return ""
    
    async def _edge_speak(self, text: str) -> str:
        """Edge TTS (free fallback)."""
        try:
            import edge_tts
            
            voice = "en-IN-NeerjaNeural"
            temp_file = tempfile.mktemp(suffix='.mp3')
            
            communicate = edge_tts.Communicate(text, voice)
            await communicate.save(temp_file)
            
            return temp_file
            
        except Exception as e:
            logger.warning(f"Edge TTS failed: {e}")
        
        return ""
    
    async def _play_audio(self, audio_file: str):
        """Play audio file (placeholder - integrate with Discord voice)."""
        # This would integrate with Discord voice client
        logger.info(f"Playing audio: {audio_file}")
        
        # Cleanup
        try:
            os.unlink(audio_file)
        except:
            pass
    
    def interrupt_speech(self):
        """Interrupt current speech."""
        self.is_speaking = False
        logger.info("Speech interrupted")
    
    def stop_listening(self):
        """Stop voice listening."""
        self.is_listening = False
        logger.info("Voice listening stopped")
    
    async def cleanup(self):
        """Cleanup resources."""
        self.stop_listening()
        if self.session:
            await self.session.close()

# Global instance
realtime_voice = RealTimeVoice()