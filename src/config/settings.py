"""Configuration management with environment variables and defaults."""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class ModelConfig:
    """Model configuration settings."""
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.95
    max_tokens: int = 200

@dataclass
class VoiceConfig:
    """Voice processing configuration."""
    stt_timeout: int = 15
    tts_timeout: int = 10
    max_audio_duration: int = 60
    sample_rate: int = 48000

@dataclass
class MemoryConfig:
    """Memory management configuration."""
    max_context_length: int = 20
    save_interval: int = 300
    cleanup_interval: int = 3600
    max_memory_mb: int = 500

@dataclass
class ConcurrencyConfig:
    """Concurrency control settings."""
    max_concurrent_requests: int = 10
    voice_lock_timeout: int = 30
    request_timeout: int = 45

class Config:
    """Main configuration class."""
    
    def __init__(self):
        self.discord_token = self._get_required("DISCORD_TOKEN")
        self.model = ModelConfig()
        self.voice = VoiceConfig()
        self.memory = MemoryConfig()
        self.concurrency = ConcurrencyConfig()
        
        # API Keys (optional)
        self.api_keys = {
            'groq': os.getenv("GROQ_API_KEY"),
            'together': os.getenv("TOGETHER_API_KEY"),
            'huggingface': os.getenv("HF_API_KEY"),
            'openrouter': os.getenv("OPENROUTER_API_KEY"),
            'elevenlabs': os.getenv("ELEVENLABS_API_KEY"),
            'anthropic': os.getenv("ANTHROPIC_API_KEY"),
            'cohere': os.getenv("COHERE_API_KEY"),
            'mistral': os.getenv("MISTRAL_API_KEY")
        }
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.log_file = os.getenv("LOG_FILE", "priya.log")
        
    def _get_required(self, key: str) -> str:
        """Get required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} not set")
        return value
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for service."""
        return self.api_keys.get(service)
    
    def has_api_key(self, service: str) -> bool:
        """Check if API key exists for service."""
        return bool(self.get_api_key(service))

# Global config instance
config = Config()