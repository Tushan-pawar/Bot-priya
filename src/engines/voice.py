"""Voice processing engine with local and cloud fallback."""
import asyncio
import aiohttp
import tempfile
import wave
import os
from typing import Dict, Optional, Any
from pathlib import Path
from ..config.settings import config
from ..utils.logging import logger, perf_logger
from ..utils.concurrency import with_timeout, with_retry

class VoiceEngine:
    """Hybrid voice processing with local and cloud fallback."""
    
    def __init__(self):
        self.stt_engines = self._init_stt_engines()
        self.tts_engines = self._init_tts_engines()
        
    def _init_stt_engines(self) -> Dict[str, Dict]:
        """Initialize speech-to-text engines."""
        engines = {}
        
        # Local Whisper (highest priority)
        try:
            from faster_whisper import WhisperModel
            engines['whisper_local'] = {
                'type': 'local',
                'priority': 1,
                'engine': WhisperModel("base", device="cpu", compute_type="int8"),
                'available': True
            }
            logger.info("Local Whisper STT initialized")
        except ImportError:
            logger.warning("faster-whisper not available")
        except Exception as e:
            logger.error(f"Failed to initialize local Whisper: {e}")
        
        # Cloud Groq Whisper
        if config.has_api_key('groq'):
            engines['groq_whisper'] = {
                'type': 'api',
                'priority': 2,
                'url': 'https://api.groq.com/openai/v1/audio/transcriptions',
                'headers': {'Authorization': f'Bearer {config.get_api_key("groq")}'},
                'available': True
            }
        
        return engines
    
    def _init_tts_engines(self) -> Dict[str, Dict]:
        """Initialize text-to-speech engines."""
        engines = {}
        
        # Local Coqui TTS (highest priority)
        try:
            from TTS.api import TTS
            # Try multilingual model first
            try:
                engines['coqui_multilingual'] = {
                    'type': 'local',
                    'priority': 1,
                    'engine': TTS("tts_models/multilingual/multi-dataset/xtts_v2"),
                    'languages': ['en', 'hi'],
                    'available': True
                }
                logger.info("Local Coqui multilingual TTS initialized")
            except:
                # Fallback to English-only model
                engines['coqui_english'] = {
                    'type': 'local',
                    'priority': 2,
                    'engine': TTS("tts_models/en/vctk/vits"),
                    'languages': ['en'],
                    'available': True
                }
                logger.info("Local Coqui English TTS initialized")
        except ImportError:
            logger.warning("TTS library not available")
        except Exception as e:
            logger.error(f"Failed to initialize local TTS: {e}")
        
        # Cloud ElevenLabs
        if config.has_api_key('elevenlabs'):
            engines['elevenlabs'] = {
                'type': 'api',
                'priority': 3,
                'url': 'https://api.elevenlabs.io/v1/text-to-speech',
                'headers': {'xi-api-key': config.get_api_key('elevenlabs')},
                'voice_id': '21m00Tcm4TlvDq8ikWAM',  # Consistent voice
                'available': True
            }
        
        return engines
    
    @with_timeout(config.voice.stt_timeout)
    @with_retry(max_retries=2)
    async def transcribe_audio(self, audio_path: str, language: str = 'auto') -> Dict[str, Any]:
        """Transcribe audio with fallback."""
        available_engines = sorted(
            [(name, engine) for name, engine in self.stt_engines.items() if engine.get('available')],
            key=lambda x: x[1]['priority']
        )
        
        for engine_name, engine_config in available_engines:
            try:
                start_time = asyncio.get_event_loop().time()
                
                if engine_config['type'] == 'local':
                    result = await self._local_stt(engine_config, audio_path, language)
                else:
                    result = await self._cloud_stt(engine_config, audio_path, language)
                
                if result and result.get('text'):
                    duration = asyncio.get_event_loop().time() - start_time
                    perf_logger.log_request("voice", f"stt_{engine_name}", duration, True)
                    logger.info(f"STT successful with {engine_name}")
                    return result
                    
            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time
                perf_logger.log_request("voice", f"stt_{engine_name}", duration, False)
                logger.warning(f"STT engine {engine_name} failed: {e}")
                continue
        
        return {'text': '', 'language': 'en', 'confidence': 0.0}
    
    async def _local_stt(self, config: Dict, audio_path: str, language: str) -> Dict[str, Any]:
        """Local speech-to-text processing."""
        loop = asyncio.get_event_loop()
        
        def transcribe():
            segments, info = config['engine'].transcribe(audio_path, language=language)
            text = " ".join([seg.text for seg in segments]).strip()
            detected_language = getattr(info, 'language', 'en')
            confidence = getattr(info, 'language_probability', 0.9)
            return {
                'text': text,
                'language': detected_language,
                'confidence': confidence
            }
        
        return await loop.run_in_executor(None, transcribe)
    
    async def _cloud_stt(self, config: Dict, audio_path: str, language: str) -> Dict[str, Any]:
        """Cloud speech-to-text processing."""
        async with aiohttp.ClientSession() as session:
            with open(audio_path, 'rb') as audio_file:
                data = aiohttp.FormData()
                data.add_field('file', audio_file, filename='audio.wav')
                data.add_field('model', 'whisper-1')
                if language != 'auto':
                    data.add_field('language', language)
                
                async with session.post(
                    config['url'], 
                    headers=config['headers'], 
                    data=data,
                    timeout=aiohttp.ClientTimeout(total=config.voice.stt_timeout)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        return {
                            'text': result.get('text', ''),
                            'language': result.get('language', 'en'),
                            'confidence': 0.9
                        }
                    else:
                        raise Exception(f"API error: {response.status}")
    
    @with_timeout(config.voice.tts_timeout)
    @with_retry(max_retries=2)
    async def synthesize_speech(self, text: str, output_path: str, voice_settings: Dict = None) -> bool:
        """Synthesize speech with fallback."""
        if not voice_settings:
            voice_settings = {
                'language': 'en',
                'emotion': 'neutral',
                'speaker': 'p273'
            }
        
        available_engines = sorted(
            [(name, engine) for name, engine in self.tts_engines.items() if engine.get('available')],
            key=lambda x: x[1]['priority']
        )
        
        for engine_name, engine_config in available_engines:
            try:
                start_time = asyncio.get_event_loop().time()
                
                if engine_config['type'] == 'local':
                    success = await self._local_tts(engine_config, text, output_path, voice_settings)
                else:
                    success = await self._cloud_tts(engine_config, text, output_path, voice_settings)
                
                duration = asyncio.get_event_loop().time() - start_time
                perf_logger.log_request("voice", f"tts_{engine_name}", duration, success)
                
                if success:
                    logger.info(f"TTS successful with {engine_name}")
                    return True
                    
            except Exception as e:
                duration = asyncio.get_event_loop().time() - start_time
                perf_logger.log_request("voice", f"tts_{engine_name}", duration, False)
                logger.warning(f"TTS engine {engine_name} failed: {e}")
                continue
        
        return False
    
    async def _local_tts(self, config: Dict, text: str, output_path: str, voice_settings: Dict) -> bool:
        """Local text-to-speech processing."""
        loop = asyncio.get_event_loop()
        
        def synthesize():
            engine = config['engine']
            language = voice_settings.get('language', 'en')
            
            # Check if engine supports the language
            if language in config.get('languages', ['en']):
                if 'multilingual' in str(type(engine)):
                    # Multilingual model
                    engine.tts_to_file(
                        text=text,
                        language=language,
                        file_path=output_path,
                        speed=voice_settings.get('speed', 1.0)
                    )
                else:
                    # English-only model
                    engine.tts_to_file(
                        text=text,
                        speaker=voice_settings.get('speaker', 'p273'),
                        file_path=output_path
                    )
                return True
            return False
        
        try:
            return await loop.run_in_executor(None, synthesize)
        except Exception:
            return False
    
    async def _cloud_tts(self, config: Dict, text: str, output_path: str, voice_settings: Dict) -> bool:
        """Cloud text-to-speech processing."""
        async with aiohttp.ClientSession() as session:
            emotion_settings = self._get_emotion_settings(voice_settings.get('emotion', 'neutral'))
            
            payload = {
                "text": text,
                "model_id": "eleven_multilingual_v2",
                "voice_settings": {
                    "stability": emotion_settings.get('stability', 0.7),
                    "similarity_boost": emotion_settings.get('similarity_boost', 0.8),
                    "style": emotion_settings.get('style', 0.2),
                    "use_speaker_boost": True
                }
            }
            
            voice_id = config.get('voice_id', '21m00Tcm4TlvDq8ikWAM')
            url = f"{config['url']}/{voice_id}"
            
            async with session.post(
                url,
                headers=config['headers'],
                json=payload,
                timeout=aiohttp.ClientTimeout(total=config.voice.tts_timeout)
            ) as response:
                if response.status == 200:
                    with open(output_path, 'wb') as f:
                        f.write(await response.read())
                    return True
                else:
                    raise Exception(f"API error: {response.status}")
    
    def _get_emotion_settings(self, emotion: str) -> Dict[str, float]:
        """Get voice settings for emotion."""
        emotion_mappings = {
            'happy': {'stability': 0.8, 'similarity_boost': 0.9, 'style': 0.3},
            'sad': {'stability': 0.6, 'similarity_boost': 0.7, 'style': 0.1},
            'excited': {'stability': 0.9, 'similarity_boost': 0.8, 'style': 0.5},
            'angry': {'stability': 0.5, 'similarity_boost': 0.6, 'style': 0.2},
            'calm': {'stability': 0.7, 'similarity_boost': 0.8, 'style': 0.1},
            'playful': {'stability': 0.8, 'similarity_boost': 0.9, 'style': 0.4},
            'worried': {'stability': 0.6, 'similarity_boost': 0.7, 'style': 0.2},
            'neutral': {'stability': 0.7, 'similarity_boost': 0.8, 'style': 0.2}
        }
        return emotion_mappings.get(emotion, emotion_mappings['neutral'])
    
    def preprocess_text_for_speech(self, text: str, voice_settings: Dict) -> str:
        """Preprocess text for natural speech."""
        processed = text
        
        # Add natural pauses
        processed = processed.replace(',', ', <break time="0.3s"/>')
        processed = processed.replace('.', '. <break time="0.5s"/>')
        processed = processed.replace('!', '! <break time="0.4s"/>')
        processed = processed.replace('?', '? <break time="0.4s"/>')
        
        # Add emphasis for important words
        emphasis_words = ['very', 'really', 'absolutely', 'definitely', 'amazing', 'incredible']
        for word in emphasis_words:
            if word in processed.lower():
                processed = processed.replace(word, f'<emphasis level="strong">{word}</emphasis>')
        
        return processed
    
    def get_status(self) -> Dict[str, Any]:
        """Get voice engine status."""
        return {
            "stt_engines": {
                name: {
                    "type": engine["type"],
                    "priority": engine["priority"],
                    "available": engine.get("available", False)
                }
                for name, engine in self.stt_engines.items()
            },
            "tts_engines": {
                name: {
                    "type": engine["type"],
                    "priority": engine["priority"],
                    "available": engine.get("available", False),
                    "languages": engine.get("languages", ["en"])
                }
                for name, engine in self.tts_engines.items()
            }
        }

# Global instance
voice_engine = VoiceEngine()