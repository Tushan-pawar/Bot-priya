"""Real-time streaming voice processing with interruption support."""
import asyncio
import pyaudio
import webrtcvad
import numpy as np
from typing import Optional, Callable, AsyncGenerator
import soundfile as sf
from io import BytesIO
import threading
from ..utils.logging import logger

class StreamingVoiceEngine:
    """Real-time voice processing with streaming and interruption."""
    
    def __init__(self):
        self.sample_rate = 16000
        self.chunk_size = 320  # 20ms at 16kHz
        self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
        
        self.is_listening = False
        self.is_speaking = False
        self.audio_buffer = []
        self.transcript_buffer = ""
        
        # Audio stream
        self.audio = pyaudio.PyAudio()
        self.stream: Optional[pyaudio.Stream] = None
        
        # Callbacks
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_partial_transcript: Optional[Callable] = None
        self.on_final_transcript: Optional[Callable] = None
    
    async def start_listening(self, user_id: str) -> None:
        """Start streaming voice recognition."""
        if self.is_listening:
            return
        
        self.is_listening = True
        self.audio_buffer = []
        self.transcript_buffer = ""
        
        try:
            # Open audio stream
            self.stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=self.chunk_size,
                stream_callback=self._audio_callback
            )
            
            self.stream.start_stream()
            logger.info(f"Started listening for user {user_id}")
            
            # Start processing loop
            asyncio.create_task(self._process_audio_stream(user_id))
            
        except Exception as e:
            logger.error(f"Failed to start listening: {e}")
            self.is_listening = False
    
    async def stop_listening(self) -> None:
        """Stop streaming voice recognition."""
        self.is_listening = False
        
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        
        logger.info("Stopped listening")
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio stream callback."""
        if self.is_listening and not self.is_speaking:
            audio_chunk = np.frombuffer(in_data, dtype=np.int16)
            self.audio_buffer.append(audio_chunk)
        
        return (None, pyaudio.paContinue)
    
    async def _process_audio_stream(self, user_id: str) -> None:
        """Process streaming audio with VAD."""
        silence_threshold = 30  # 30 chunks of silence
        silence_count = 0
        speech_started = False
        speech_buffer = []
        
        while self.is_listening:
            try:
                if not self.audio_buffer:
                    await asyncio.sleep(0.01)
                    continue
                
                # Get audio chunk
                audio_chunk = self.audio_buffer.pop(0)
                
                # Voice Activity Detection
                is_speech = self._detect_speech(audio_chunk)
                
                if is_speech:
                    silence_count = 0
                    
                    if not speech_started:
                        speech_started = True
                        speech_buffer = []
                        if self.on_speech_start:
                            await self.on_speech_start(user_id)
                    
                    speech_buffer.append(audio_chunk)
                    
                    # Process partial transcript every 1 second
                    if len(speech_buffer) % 50 == 0:  # ~1 second
                        partial_text = await self._transcribe_chunk(speech_buffer[-50:])
                        if partial_text and self.on_partial_transcript:
                            await self.on_partial_transcript(user_id, partial_text)
                
                else:
                    silence_count += 1
                    
                    if speech_started and silence_count >= silence_threshold:
                        # End of speech detected
                        speech_started = False
                        
                        if speech_buffer:
                            final_text = await self._transcribe_chunk(speech_buffer)
                            if final_text:
                                if self.on_final_transcript:
                                    await self.on_final_transcript(user_id, final_text)
                                
                                if self.on_speech_end:
                                    await self.on_speech_end(user_id)
                        
                        speech_buffer = []
                        silence_count = 0
                
            except Exception as e:
                logger.error(f"Error processing audio stream: {e}")
                await asyncio.sleep(0.1)
    
    def _detect_speech(self, audio_chunk: np.ndarray) -> bool:
        """Detect speech using WebRTC VAD."""
        try:
            # Convert to bytes
            audio_bytes = audio_chunk.tobytes()
            
            # VAD requires specific frame sizes
            if len(audio_bytes) == self.chunk_size * 2:  # 16-bit samples
                return self.vad.is_speech(audio_bytes, self.sample_rate)
            
            return False
            
        except Exception:
            return False
    
    async def _transcribe_chunk(self, audio_chunks: list) -> str:
        """Transcribe audio chunk using Whisper."""
        try:
            # Combine audio chunks
            audio_data = np.concatenate(audio_chunks)
            
            # Convert to float32 for Whisper
            audio_float = audio_data.astype(np.float32) / 32768.0
            
            # Save to temporary buffer
            buffer = BytesIO()
            sf.write(buffer, audio_float, self.sample_rate, format='WAV')
            buffer.seek(0)
            
            # Transcribe using existing voice engine
            from ..engines.voice import voice_engine
            
            # Save buffer to temp file
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(buffer.getvalue())
                temp_path = temp_file.name
            
            result = await voice_engine.transcribe_audio(temp_path)
            
            # Cleanup
            import os
            os.unlink(temp_path)
            
            return result.get('text', '').strip()
            
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return ""
    
    async def interrupt_speech(self) -> None:
        """Interrupt current TTS playback."""
        if self.is_speaking:
            self.is_speaking = False
            logger.info("Speech interrupted by user")
    
    async def speak_with_interruption(
        self, 
        text: str, 
        voice_client, 
        voice_settings: dict = None
    ) -> bool:
        """Speak with interruption support."""
        self.is_speaking = True
        
        try:
            # Generate TTS
            from ..engines.voice import voice_engine
            import tempfile
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                output_path = temp_file.name
            
            success = await voice_engine.synthesize_speech(text, output_path, voice_settings)
            
            if not success:
                return False
            
            # Play with interruption check
            source = discord.FFmpegPCMAudio(output_path)
            voice_client.play(source)
            
            # Monitor for interruption
            while voice_client.is_playing() and self.is_speaking:
                await asyncio.sleep(0.1)
            
            if not self.is_speaking:
                voice_client.stop()
            
            # Cleanup
            import os
            os.unlink(output_path)
            
            return True
            
        except Exception as e:
            logger.error(f"TTS with interruption failed: {e}")
            return False
        
        finally:
            self.is_speaking = False

# Global instance
streaming_voice = StreamingVoiceEngine()