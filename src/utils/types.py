"""Type definitions and protocols for the Priya bot."""
from typing import Protocol, Dict, Any, List, Optional, Union
from abc import ABC, abstractmethod

class VoiceEngine(Protocol):
    """Protocol for voice processing engines."""
    
    async def transcribe_audio(self, audio_path: str, language: str = 'auto') -> Dict[str, Any]:
        """Transcribe audio to text."""
        ...
    
    async def synthesize_speech(self, text: str, output_path: str, voice_settings: Dict = None) -> bool:
        """Synthesize text to speech."""
        ...

class LLMProvider(Protocol):
    """Protocol for LLM providers."""
    
    async def generate_response(self, messages: List[Dict], temperature: float = 0.95) -> str:
        """Generate response from messages."""
        ...
    
    def get_status(self) -> Dict[str, Any]:
        """Get provider status."""
        ...

class MemorySystem(Protocol):
    """Protocol for memory systems."""
    
    async def save_memory(self, force: bool = False) -> None:
        """Save memory to persistent storage."""
        ...
    
    def get_user_context(self, user_id: str) -> Any:
        """Get user context."""
        ...

# Type aliases
MessageHistory = List[Dict[str, Union[str, float]]]
UserContext = Dict[str, Any]
VoiceSettings = Dict[str, Union[str, float, bool]]
ModelResponse = Dict[str, Union[str, float, bool, Dict]]