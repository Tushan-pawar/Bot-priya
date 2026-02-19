"""Comprehensive failure recovery and hardening system."""
import asyncio
import time
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from ..utils.logging import logger

class FailureType(Enum):
    LLM_UNAVAILABLE = "llm_unavailable"
    OLLAMA_TIMEOUT = "ollama_timeout"
    VECTOR_DB_FAILURE = "vector_db_failure"
    TTS_FAILURE = "tts_failure"
    VOICE_DISCONNECT = "voice_disconnect"
    TOOL_EXECUTION_ERROR = "tool_execution_error"
    MEMORY_ERROR = "memory_error"
    NETWORK_ERROR = "network_error"

@dataclass
class FailureContext:
    """Context information for failures."""
    failure_type: FailureType
    error: Exception
    user_id: Optional[str] = None
    operation: Optional[str] = None
    retry_count: int = 0
    metadata: Dict[str, Any] = None

class FailureRecoverySystem:
    """Comprehensive failure recovery and hardening."""
    
    def __init__(self):
        self.failure_handlers: Dict[FailureType, Callable] = {}
        self.failure_stats: Dict[FailureType, int] = {}
        self.circuit_breakers: Dict[str, Dict] = {}
        self.fallback_responses = self._init_fallback_responses()
        
        # Register default handlers
        self._register_default_handlers()
    
    def _init_fallback_responses(self) -> Dict[FailureType, List[str]]:
        """Initialize fallback responses for different failure types."""
        return {
            FailureType.LLM_UNAVAILABLE: [
                "Arre yaar, my brain is taking a break! 🧠 Try again in a moment?",
                "All my AI models are busy right now. Give me a sec! ⏰",
                "Technical difficulties with my thinking cap! 🎩 One moment please..."
            ],
            FailureType.OLLAMA_TIMEOUT: [
                "My local brain is being slow today! 🐌 Let me try a different approach...",
                "Ollama is taking its sweet time! Using backup systems... 🔄"
            ],
            FailureType.VECTOR_DB_FAILURE: [
                "My memory is a bit fuzzy right now! 🤔 But I can still chat with you!",
                "Memory system hiccup! Don't worry, I'll remember this conversation. 💭"
            ],
            FailureType.TTS_FAILURE: [
                "Can't speak right now, but I can still type! 💬",
                "Voice box needs a tune-up! Text mode it is! ⌨️"
            ],
            FailureType.VOICE_DISCONNECT: [
                "Oops, voice connection dropped! 📞 Try rejoining the channel?",
                "Voice chat disconnected! I'm still here in text though! 💬"
            ],
            FailureType.TOOL_EXECUTION_ERROR: [
                "That tool isn't working right now! 🔧 Let me help you another way.",
                "Tool malfunction! But I can still assist you manually! 🛠️"
            ],
            FailureType.MEMORY_ERROR: [
                "Memory glitch! But I'm still here and ready to chat! 🤖",
                "Having a senior moment! 👵 But let's continue our conversation!"
            ],
            FailureType.NETWORK_ERROR: [
                "Network hiccup! 🌐 Using offline mode for now...",
                "Internet is being moody! 📡 But local systems are working fine!"
            ]
        }
    
    def _register_default_handlers(self):
        """Register default failure handlers."""
        self.register_handler(FailureType.LLM_UNAVAILABLE, self._handle_llm_failure)
        self.register_handler(FailureType.OLLAMA_TIMEOUT, self._handle_ollama_timeout)
        self.register_handler(FailureType.VECTOR_DB_FAILURE, self._handle_vector_db_failure)
        self.register_handler(FailureType.TTS_FAILURE, self._handle_tts_failure)
        self.register_handler(FailureType.VOICE_DISCONNECT, self._handle_voice_disconnect)
        self.register_handler(FailureType.TOOL_EXECUTION_ERROR, self._handle_tool_error)
        self.register_handler(FailureType.MEMORY_ERROR, self._handle_memory_error)
        self.register_handler(FailureType.NETWORK_ERROR, self._handle_network_error)
    
    def register_handler(self, failure_type: FailureType, handler: Callable):
        """Register a failure handler."""
        self.failure_handlers[failure_type] = handler
        self.failure_stats[failure_type] = 0
    
    async def handle_failure(self, context: FailureContext) -> Dict[str, Any]:
        """Handle a failure with appropriate recovery strategy."""
        self.failure_stats[context.failure_type] += 1
        
        logger.error(
            f"Handling failure: {context.failure_type.value}",
            extra={
                'failure_type': context.failure_type.value,
                'error': str(context.error),
                'user_id': context.user_id,
                'operation': context.operation,
                'retry_count': context.retry_count
            }
        )
        
        # Check circuit breaker
        if self._is_circuit_open(context.failure_type.value):
            return self._circuit_breaker_response(context)
        
        # Try specific handler
        if context.failure_type in self.failure_handlers:
            try:
                result = await self.failure_handlers[context.failure_type](context)
                if result.get('success'):
                    self._reset_circuit_breaker(context.failure_type.value)
                    return result
            except Exception as handler_error:
                logger.error(f"Failure handler failed: {handler_error}")
        
        # Fallback to generic response
        return self._generic_fallback(context)
    
    def _is_circuit_open(self, operation: str) -> bool:
        """Check if circuit breaker is open for operation."""
        if operation not in self.circuit_breakers:
            return False
        
        breaker = self.circuit_breakers[operation]
        if breaker['state'] == 'open':
            if time.time() - breaker['last_failure'] > breaker['timeout']:
                breaker['state'] = 'half-open'
                return False
            return True
        
        return False
    
    def _trip_circuit_breaker(self, operation: str):
        """Trip circuit breaker for operation."""
        if operation not in self.circuit_breakers:
            self.circuit_breakers[operation] = {
                'state': 'closed',
                'failure_count': 0,
                'last_failure': 0,
                'timeout': 60  # 1 minute
            }
        
        breaker = self.circuit_breakers[operation]
        breaker['failure_count'] += 1
        breaker['last_failure'] = time.time()
        
        if breaker['failure_count'] >= 5:  # Trip after 5 failures
            breaker['state'] = 'open'
            logger.warning(f"Circuit breaker tripped for {operation}")
    
    def _reset_circuit_breaker(self, operation: str):
        """Reset circuit breaker for operation."""
        if operation in self.circuit_breakers:
            self.circuit_breakers[operation]['state'] = 'closed'
            self.circuit_breakers[operation]['failure_count'] = 0
    
    def _circuit_breaker_response(self, context: FailureContext) -> Dict[str, Any]:
        """Response when circuit breaker is open."""
        return {
            'success': False,
            'response': "System is temporarily unavailable. Please try again later. 🔧",
            'fallback': True,
            'circuit_breaker': True
        }
    
    def _generic_fallback(self, context: FailureContext) -> Dict[str, Any]:
        """Generic fallback response."""
        import random
        responses = self.fallback_responses.get(
            context.failure_type, 
            ["Something went wrong, but I'm still here! 🤖"]
        )
        
        return {
            'success': False,
            'response': random.choice(responses),
            'fallback': True,
            'should_retry': context.retry_count < 2
        }
    
    # Specific failure handlers
    async def _handle_llm_failure(self, context: FailureContext) -> Dict[str, Any]:
        """Handle LLM unavailability."""
        try:
            # Try emergency fallback LLM
            from ..models.llm_fallback import llm_system
            
            # Use simplest available provider
            available_providers = llm_system.get_available_providers()
            if available_providers:
                # Try with minimal prompt
                simple_messages = [{"role": "user", "content": "Hi"}]
                response = await llm_system.generate_response(simple_messages)
                if response:
                    return {'success': True, 'response': response}
            
            # If all else fails, use pre-generated responses
            import random
            responses = [
                "Hey! I'm having some technical difficulties but I'm still here! 😊",
                "My AI brain is taking a coffee break! ☕ But I can still chat!",
                "All systems are go... well, mostly! 🚀 How can I help?"
            ]
            
            return {'success': True, 'response': random.choice(responses)}
            
        except Exception as llm_error:
            logger.error(f"LLM fallback failed: {llm_error}")
            return self._generic_fallback(context)
    
    async def _handle_ollama_timeout(self, context: FailureContext) -> Dict[str, Any]:
        """Handle Ollama timeout."""
        try:
            # Switch to cloud providers
            from ..models.llm_fallback import llm_system
            
            # Filter out local providers
            cloud_providers = [p for p in llm_system.get_available_providers() if p.url != "local"]
            
            if cloud_providers:
                # Try cloud provider
                messages = [{"role": "user", "content": "Hello"}]
                response = await llm_system.generate_response(messages)
                if response:
                    return {'success': True, 'response': response}
            
            return self._generic_fallback(context)
            
        except Exception as ollama_error:
            logger.error(f"Ollama timeout fallback failed: {ollama_error}")
            return self._generic_fallback(context)
    
    def _handle_vector_db_failure(self, context: FailureContext) -> Dict[str, Any]:
        """Handle vector database failure."""
        # Continue without memory retrieval
        return {
            'success': True,
            'response': "I'm having trouble accessing my memories, but let's continue our chat! 💭",
            'disable_memory': True
        }
    
    def _handle_tts_failure(self, context: FailureContext) -> Dict[str, Any]:
        """Handle TTS failure."""
        return {
            'success': True,
            'response': "Voice synthesis is down, but I can still type! 💬",
            'disable_voice': True
        }
    
    def _handle_voice_disconnect(self, context: FailureContext) -> Dict[str, Any]:
        """Handle voice disconnection."""
        return {
            'success': True,
            'response': "Voice connection lost! I'm still here in text chat though! 📱",
            'reconnect_voice': True
        }
    
    def _handle_tool_error(self, context: FailureContext) -> Dict[str, Any]:
        """Handle tool execution error."""
        return {
            'success': True,
            'response': "That tool isn't working right now, but I can help you manually! 🛠️",
            'disable_tools': True
        }
    
    def _handle_memory_error(self, context: FailureContext) -> Dict[str, Any]:
        """Handle memory system error."""
        return {
            'success': True,
            'response': "Having a memory hiccup! But I'm still here and ready to help! 🤖",
            'disable_memory': True
        }
    
    def _handle_network_error(self, context: FailureContext) -> Dict[str, Any]:
        """Handle network error."""
        # Switch to local-only mode temporarily
        return {
            'success': True,
            'response': "Network issues detected! Switching to offline mode... 📡",
            'local_only': True
        }
    
    def get_failure_stats(self) -> Dict[str, Any]:
        """Get failure statistics."""
        return {
            'total_failures': sum(self.failure_stats.values()),
            'failure_breakdown': {ft.value: count for ft, count in self.failure_stats.items()},
            'circuit_breakers': {
                op: {
                    'state': cb['state'],
                    'failure_count': cb['failure_count'],
                    'last_failure': cb['last_failure']
                }
                for op, cb in self.circuit_breakers.items()
            }
        }

# Global instance
failure_recovery = FailureRecoverySystem()