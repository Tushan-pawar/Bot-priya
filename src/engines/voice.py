"""Real-time voice processing engine with streaming and VAD."""
import asyncio
import aiohttp
import tempfile
import wave
import os
import time
from typing import Dict, Optional, Any, Callable
from pathlib import Path
from ..config.settings import config
from ..utils.logging import logger, perf_logger
from ..utils.concurrency import with_timeout, with_retry

# Voice Activity Detection
try:
    import webrtcvad
    VAD_AVAILABLE = True
except ImportError:
    VAD_AVAILABLE = False
    logger.warning("webrtcvad not available - no voice activity detection")

class RealTimeVoiceEngine:
    """Real-time voice processing with <800ms total latency."""
    
    def __init__(self):
        self.stt_engines = self._init_stt_engines()
        self.tts_engines = self._init_tts_engines()
        self.session = None  # Reusable HTTP session
        self.vad = None
        self.is_speaking = False
        self.audio_cache = {}  # Cache for TTS
        
        # Callbacks for real-time events
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable] = None
        self.on_transcript_ready: Optional[Callable] = None
        
        if VAD_AVAILABLE:
            self.vad = webrtcvad.Vad(2)  # Aggressiveness level 2
    
    async def start_session(self):
        """Initialize HTTP session for API calls."""
        if not self.session or self.session.closed:
            timeout = aiohttp.ClientTimeout(total=2, connect=0.5)
            connector = aiohttp.TCPConnector(
                limit=20, 
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            self.session = aiohttp.ClientSession(
                timeout=timeout, 
                connector=connector
            )
            await asyncio.sleep(0)  # Ensure async behavior
    
    def detect_voice_activity(self, audio_data: bytes, sample_rate: int = 16000) -> bool:
        """Detect if audio contains speech."""
        if not self.vad:
            return True  # Assume speech if VAD not available
        
        try:
            # VAD expects 10, 20, or 30ms frames
            frame_duration = 20  # ms
            frame_size = int(sample_rate * frame_duration / 1000)
            
            if len(audio_data) >= frame_size * 2:  # 16-bit audio
                frame = audio_data[:frame_size * 2]
                return self.vad.is_speech(frame, sample_rate)
        except Exception as e:
            logger.warning(f"VAD error: {e}")
        
        return True
    
    async def stream_transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Ultra-fast transcription with parallel processing."""
        await self.start_session()
        
        # Race the two fastest STT engines
        tasks = []
        
        # Groq Whisper (fastest cloud)
        if 'groq_whisper' in self.stt_engines:
            tasks.append(asyncio.create_task(
                self._groq_transcribe(audio_path)
            ))
        
        # Local Whisper (if available)
        if 'whisper_local' in self.stt_engines:
            tasks.append(asyncio.create_task(
                self._local_transcribe(audio_path)
            ))
        
        if not tasks:
            return {'text': '', 'confidence': 0.0}
        
        try:
            # Return first result within 1.5 seconds
            done, pending = await asyncio.wait(
                tasks, 
                return_when=asyncio.FIRST_COMPLETED,
                timeout=1.5
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get first successful result
            for task in done:
                try:
                    result = await task
                    if result and result.get('text'):
                        return result
                except Exception as e:
                    logger.warning(f"STT task failed: {e}")
                    continue
        
        except asyncio.TimeoutError:
            logger.warning("STT timeout - all engines too slow")
        
        return {'text': '', 'confidence': 0.0}
    
    async def _groq_transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Groq Whisper transcription."""
        try:
            import aiofiles
            async with aiofiles.open(audio_path, 'rb') as audio_file:
                audio_data = await audio_file.read()
                data = aiohttp.FormData()
                data.add_field('file', audio_data, filename='audio.wav')
                data.add_field('model', 'whisper-1')
                data.add_field('response_format', 'json')
                
                async with self.session.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    headers={'Authorization': f'Bearer {config.get_api_key("groq")}'},
                    data=data
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {'text': result.get('text', '').strip(), 'confidence': 0.9}
        except Exception as e:
            logger.warning(f"Groq STT failed: {e}")
        return {'text': '', 'confidence': 0.0}
    
    async def _local_transcribe(self, audio_path: str) -> Dict[str, Any]:
        """Local Whisper transcription."""
        try:
            from faster_whisper import WhisperModel
            
            # Lazy load model
            if not hasattr(self, '_whisper_model'):
                self._whisper_model = WhisperModel("base", device="cpu", compute_type="int8")
            
            loop = asyncio.get_event_loop()
            
            def transcribe():
                segments, info = self._whisper_model.transcribe(audio_path)
                text = " ".join([seg.text for seg in segments]).strip()
                return {
                    'text': text,
                    'confidence': getattr(info, 'language_probability', 0.8)
                }
            
            return await loop.run_in_executor(None, transcribe)
            
        except ImportError as e:
            logger.warning(f"Local STT failed: {e}")
        
        return {'text': '', 'confidence': 0.0}
    
    async def stream_synthesize(self, text: str, output_path: str, interrupt_check: Callable = None) -> bool:
        """Ultra-fast TTS with streaming and interruption."""
        await self.start_session()
        cache_key = hash(text)
        if await self._try_cache(cache_key, output_path):
            return True
        tasks = self._create_tts_tasks(text, output_path, interrupt_check)
        if not tasks:
            return False
        return await self._race_tts_engines(tasks, cache_key, output_path)
    
    async def _try_cache(self, cache_key: int, output_path: str) -> bool:
        """Try to use cached audio."""
        if cache_key in self.audio_cache:
            try:
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, lambda: __import__('shutil').copy2(self.audio_cache[cache_key], output_path))
                return True
            except (IOError, OSError):
                pass
        return False
    
    def _create_tts_tasks(self, text: str, output_path: str, interrupt_check: Callable):
        """Create TTS tasks for racing."""
        tasks = []
        if 'elevenlabs' in self.tts_engines and config.has_api_key('elevenlabs'):
            tasks.append(asyncio.create_task(self._elevenlabs_tts(text, output_path, interrupt_check)))
        tasks.append(asyncio.create_task(self._edge_tts(text, output_path, interrupt_check)))
        return tasks
    
    async def _race_tts_engines(self, tasks, cache_key: int, output_path: str) -> bool:
        """Race TTS engines and return first result."""
        try:
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=2.0)
            for task in pending:
                task.cancel()
            for task in done:
                try:
                    if await task:
                        if len(self.audio_cache) > 50:
                            self.audio_cache.clear()
                        self.audio_cache[cache_key] = output_path
                        return True
                except Exception as e:
                    logger.warning(f"TTS task failed: {e}")
        except asyncio.TimeoutError:
            logger.warning("TTS timeout - all engines too slow")
        return False
    
    async def _elevenlabs_tts(self, text: str, output_path: str, interrupt_check: Callable) -> bool:
        """ElevenLabs TTS with streaming."""
        try:
            import aiofiles
            payload = {
                "text": text,
                "model_id": "eleven_turbo_v2",
                "voice_settings": {"stability": 0.7, "similarity_boost": 0.8, "style": 0.2, "use_speaker_boost": True}
            }
            voice_id = "21m00Tcm4TlvDq8ikWAM"
            url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
            async with self.session.post(url, headers={'xi-api-key': config.get_api_key('elevenlabs')}, json=payload) as response:
                if response.status == 200:
                    async with aiofiles.open(output_path, 'wb') as f:
                        async for chunk in response.content.iter_chunked(1024):
                            if interrupt_check and interrupt_check():
                                return False
                            await f.write(chunk)
                    return True
        except Exception as e:
            logger.warning(f"ElevenLabs TTS failed: {e}")
        return False
    
    async def _edge_tts(self, text: str, output_path: str, interrupt_check: Callable) -> bool:
        """Edge TTS (free, fast fallback)."""
        try:
            import edge_tts
            import aiofiles
            voice = "en-IN-NeerjaNeural"
            communicate = edge_tts.Communicate(text, voice)
            async with aiofiles.open(output_path, 'wb') as f:
                async for chunk in communicate.stream():
                    if interrupt_check and interrupt_check():
                        return False
                    if chunk["type"] == "audio":
                        await f.write(chunk["data"])
            return True
        except Exception as e:
            logger.warning(f"Edge TTS failed: {e}")
        return False
    
    def interrupt_speech(self):
        """Interrupt current speech synthesis."""
        self.is_speaking = False
        if self.on_speech_end:
            self._interrupt_task = asyncio.create_task(self.on_speech_end())
    
    async def process_voice_message(self, audio_path: str, response_callback: Callable) -> bool:
        """Complete voice processing pipeline."""
        start_time = time.time()
        
        try:
            # Step 1: Transcribe (target: <300ms)
            transcript_result = await self.stream_transcribe(audio_path)
            transcript_time = time.time() - start_time
            
            if not transcript_result.get('text'):
                return False
            
            transcript = transcript_result['text']
            logger.info(f"Transcribed in {transcript_time*1000:.0f}ms: {transcript}")
            
            # Step 2: Generate response (target: <400ms)
            response_start = time.time()
            response_text = await response_callback(transcript)
            response_time = time.time() - response_start
            
            if not response_text:
                return False
            
            logger.info(f"Generated response in {response_time*1000:.0f}ms: {response_text}")
            
            # Step 3: Synthesize speech (target: <300ms)
            tts_start = time.time()
            import aiofiles.tempfile
            async with aiofiles.tempfile.NamedTemporaryFile(suffix='.wav', delete=False, mode='wb') as tmp:
                output_path = tmp.name
            
            success = await self.stream_synthesize(response_text, output_path, lambda: not self.is_speaking)
            
            tts_time = time.time() - tts_start
            total_time = time.time() - start_time
            
            logger.info(f"Voice pipeline completed in {total_time*1000:.0f}ms (STT: {transcript_time*1000:.0f}ms, LLM: {response_time*1000:.0f}ms, TTS: {tts_time*1000:.0f}ms)")
            
            return success and os.path.exists(output_path)
            
        except Exception as e:
            logger.error(f"Voice processing failed: {e}")
            return False
    
    def _init_stt_engines(self) -> Dict[str, Dict]:
        """Initialize fastest STT engines."""
        engines = {}
        
        # Groq Whisper (fastest cloud)
        if config.has_api_key('groq'):
            engines['groq_whisper'] = {
                'type': 'api',
                'priority': 1,
                'available': True
            }
        
        # Local Whisper (fallback)
        try:
            from faster_whisper import WhisperModel
            engines['whisper_local'] = {
                'type': 'local',
                'priority': 2,
                'available': True
            }
        except ImportError:
            pass
        
        return engines
    
    def _init_tts_engines(self) -> Dict[str, Dict]:
        """Initialize fastest TTS engines."""
        engines = {}
        
        # ElevenLabs (fastest, best quality)
        if config.has_api_key('elevenlabs'):
            engines['elevenlabs'] = {
                'type': 'api',
                'priority': 1,
                'available': True
            }
        
        # Edge TTS (free, fast)
        try:
            import edge_tts
            engines['edge_tts'] = {
                'type': 'local',
                'priority': 2,
                'available': True
            }
        except ImportError:
            pass
        
        return engines
    
    async def cleanup(self):
        """Cleanup resources."""
        if self.session and not self.session.closed:
            await self.session.close()
        self.audio_cache.clear()

# Global instance
voice_engine = RealTimeVoiceEngine()