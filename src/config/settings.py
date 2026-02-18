"""Enhanced configuration with validation and schema."""
import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path
import json
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

load_dotenv()

class ModelConfigSchema(BaseModel):
    """Model configuration schema."""
    timeout: int = Field(default=30, ge=5, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)
    temperature: float = Field(default=0.95, ge=0.0, le=2.0)
    max_tokens: int = Field(default=200, ge=10, le=4000)

class VoiceConfigSchema(BaseModel):
    """Voice processing configuration schema."""
    stt_timeout: int = Field(default=15, ge=5, le=60)
    tts_timeout: int = Field(default=10, ge=5, le=30)
    max_audio_duration: int = Field(default=60, ge=10, le=300)
    sample_rate: int = Field(default=48000, ge=16000, le=48000)

class MemoryConfigSchema(BaseModel):
    """Memory management configuration schema."""
    max_context_length: int = Field(default=20, ge=5, le=100)
    save_interval: int = Field(default=300, ge=60, le=3600)
    cleanup_interval: int = Field(default=3600, ge=300, le=86400)
    max_memory_mb: int = Field(default=500, ge=100, le=2000)

class ConcurrencyConfigSchema(BaseModel):
    """Concurrency control settings schema."""
    max_concurrent_requests: int = Field(default=10, ge=1, le=100)
    voice_lock_timeout: int = Field(default=30, ge=5, le=300)
    request_timeout: int = Field(default=45, ge=10, le=300)

class SecurityConfigSchema(BaseModel):
    """Security configuration schema."""
    enable_prompt_injection_detection: bool = True
    enable_input_sanitization: bool = True
    enable_output_filtering: bool = True
    max_input_length: int = Field(default=4000, ge=100, le=10000)

class ConfigValidationError(Exception):
    """Configuration validation error."""
    pass

class Config:
    """Main configuration class with validation."""
    
    def __init__(self):
        self._validate_environment()
        
        self.discord_token = self._get_required("DISCORD_TOKEN")
        
        # Load and validate configurations
        self.model = self._load_model_config()
        self.voice = self._load_voice_config()
        self.memory = self._load_memory_config()
        self.concurrency = self._load_concurrency_config()
        self.security = self._load_security_config()
        
        # API Keys (optional)
        self.api_keys = self._load_api_keys()
        
        # Logging configuration
        self.log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        self.log_file = os.getenv("LOG_FILE", "priya.log")
        
        # Validate log level
        if self.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            raise ConfigValidationError(f"Invalid LOG_LEVEL: {self.log_level}")
        
        # Local-only mode
        self.local_only = os.getenv("LOCAL_ONLY", "false").lower() == "true"
        
        # Validate configuration
        self._validate_config()
    
    def _validate_environment(self):
        """Validate environment setup."""
        # Check Python version
        import sys
        if sys.version_info < (3, 8):
            raise ConfigValidationError("Python 3.8+ required")
        
        # Check required directories
        required_dirs = ["data", "logs"]
        for dir_name in required_dirs:
            Path(dir_name).mkdir(exist_ok=True)
    
    def _load_model_config(self) -> ModelConfigSchema:
        """Load and validate model configuration."""
        config_data = {
            "timeout": int(os.getenv("MODEL_TIMEOUT", "30")),
            "max_retries": int(os.getenv("MODEL_MAX_RETRIES", "3")),
            "temperature": float(os.getenv("MODEL_TEMPERATURE", "0.95")),
            "max_tokens": int(os.getenv("MODEL_MAX_TOKENS", "200"))
        }
        
        try:
            return ModelConfigSchema(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Invalid model configuration: {e}")
    
    def _load_voice_config(self) -> VoiceConfigSchema:
        """Load and validate voice configuration."""
        config_data = {
            "stt_timeout": int(os.getenv("STT_TIMEOUT", "15")),
            "tts_timeout": int(os.getenv("TTS_TIMEOUT", "10")),
            "max_audio_duration": int(os.getenv("MAX_AUDIO_DURATION", "60")),
            "sample_rate": int(os.getenv("SAMPLE_RATE", "48000"))
        }
        
        try:
            return VoiceConfigSchema(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Invalid voice configuration: {e}")
    
    def _load_memory_config(self) -> MemoryConfigSchema:
        """Load and validate memory configuration."""
        config_data = {
            "max_context_length": int(os.getenv("MAX_CONTEXT_LENGTH", "20")),
            "save_interval": int(os.getenv("MEMORY_SAVE_INTERVAL", "300")),
            "cleanup_interval": int(os.getenv("MEMORY_CLEANUP_INTERVAL", "3600")),
            "max_memory_mb": int(os.getenv("MAX_MEMORY_MB", "500"))
        }
        
        try:
            return MemoryConfigSchema(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Invalid memory configuration: {e}")
    
    def _load_concurrency_config(self) -> ConcurrencyConfigSchema:
        """Load and validate concurrency configuration."""
        config_data = {
            "max_concurrent_requests": int(os.getenv("MAX_CONCURRENT_REQUESTS", "10")),
            "voice_lock_timeout": int(os.getenv("VOICE_LOCK_TIMEOUT", "30")),
            "request_timeout": int(os.getenv("REQUEST_TIMEOUT", "45"))
        }
        
        try:
            return ConcurrencyConfigSchema(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Invalid concurrency configuration: {e}")
    
    def _load_security_config(self) -> SecurityConfigSchema:
        """Load and validate security configuration."""
        config_data = {
            "enable_prompt_injection_detection": os.getenv("ENABLE_PROMPT_INJECTION_DETECTION", "true").lower() == "true",
            "enable_input_sanitization": os.getenv("ENABLE_INPUT_SANITIZATION", "true").lower() == "true",
            "enable_output_filtering": os.getenv("ENABLE_OUTPUT_FILTERING", "true").lower() == "true",
            "max_input_length": int(os.getenv("MAX_INPUT_LENGTH", "4000"))
        }
        
        try:
            return SecurityConfigSchema(**config_data)
        except Exception as e:
            raise ConfigValidationError(f"Invalid security configuration: {e}")
    
    def _load_api_keys(self) -> Dict[str, Optional[str]]:
        """Load API keys with validation."""
        api_keys = {
            'groq': os.getenv("GROQ_API_KEY"),
            'together': os.getenv("TOGETHER_API_KEY"),
            'huggingface': os.getenv("HUGGINGFACE_API_KEY"),
            'openrouter': os.getenv("OPENROUTER_API_KEY"),
            'elevenlabs': os.getenv("ELEVENLABS_API_KEY"),
            'anthropic': os.getenv("ANTHROPIC_API_KEY"),
            'cohere': os.getenv("COHERE_API_KEY"),
            'mistral': os.getenv("MISTRAL_API_KEY")
        }
        
        # Validate API key formats
        for service, key in api_keys.items():
            if key and len(key) < 10:
                raise ConfigValidationError(f"Invalid API key format for {service}")
        
        return api_keys
    
    def _get_required(self, key: str) -> str:
        """Get required environment variable."""
        value = os.getenv(key)
        if not value:
            raise ConfigValidationError(f"Required environment variable {key} not set")
        return value
    
    def _validate_config(self):
        """Validate overall configuration consistency."""
        # Check if local-only mode has necessary components
        if self.local_only:
            try:
                import ollama
                ollama.list()
            except:
                raise ConfigValidationError("LOCAL_ONLY mode requires Ollama to be installed and running")
        
        # Warn if no API keys in non-local mode
        if not self.local_only and not any(self.api_keys.values()):
            import warnings
            warnings.warn("No API keys configured. Bot will only work with local models.")
        
        # Validate memory limits
        if self.memory.max_memory_mb < 100:
            raise ConfigValidationError("MAX_MEMORY_MB must be at least 100MB")
        
        # Validate concurrency limits
        if self.concurrency.max_concurrent_requests > 50:
            import warnings
            warnings.warn("High concurrent request limit may cause performance issues")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for service."""
        return self.api_keys.get(service)
    
    def has_api_key(self, service: str) -> bool:
        """Check if API key exists for service."""
        return bool(self.get_api_key(service))
    
    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary (excluding sensitive data)."""
        return {
            "model": self.model.dict(),
            "voice": self.voice.dict(),
            "memory": self.memory.dict(),
            "concurrency": self.concurrency.dict(),
            "security": self.security.dict(),
            "log_level": self.log_level,
            "local_only": self.local_only,
            "api_keys_configured": [k for k, v in self.api_keys.items() if v]
        }

# Global config instance with error handling
try:
    config = Config()
except ConfigValidationError as e:
    print(f"❌ Configuration Error: {e}")
    print("Please check your environment variables and try again.")
    exit(1)
except Exception as e:
    print(f"❌ Unexpected configuration error: {e}")
    exit(1)