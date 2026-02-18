"""LLM fallback system with multiple providers and health monitoring."""
import asyncio
import aiohttp
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from ..config.settings import config
from ..utils.logging import logger, perf_logger
from ..utils.concurrency import with_timeout, with_retry

class ModelStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"
    UNKNOWN = "unknown"

@dataclass
class ModelProvider:
    name: str
    model: str
    url: str
    headers: Dict[str, str]
    priority: int
    daily_limit: int
    used_today: int = 0
    status: ModelStatus = ModelStatus.UNKNOWN
    last_check: float = 0
    avg_response_time: float = 0
    error_count: int = 0

class LLMFallbackSystem:
    """Multi-provider LLM system with automatic failover."""
    
    def __init__(self):
        self.providers = self._init_providers()
        self.health_check_interval = 300  # 5 minutes
        self.last_health_check = 0
        
    def _init_providers(self) -> List[ModelProvider]:
        """Initialize all available providers."""
        providers = []
        
        # Local Ollama (highest priority if available)
        if self._check_ollama():
            providers.extend([
                ModelProvider("ollama_llama32", "llama3.2", "local", {}, 1, 999999),
                ModelProvider("ollama_llama31", "llama3.1", "local", {}, 2, 999999),
                ModelProvider("ollama_mistral", "mistral", "local", {}, 3, 999999)
            ])
        
        # Cloud providers
        if config.has_api_key('groq'):
            providers.extend([
                ModelProvider(
                    "groq_llama32", "llama-3.2-3b-preview",
                    "https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization": f"Bearer {config.get_api_key('groq')}"},
                    5, 6000
                ),
                ModelProvider(
                    "groq_llama31", "llama-3.1-8b-instant",
                    "https://api.groq.com/openai/v1/chat/completions",
                    {"Authorization": f"Bearer {config.get_api_key('groq')}"},
                    6, 6000
                )
            ])
        
        if config.has_api_key('together'):
            providers.extend([
                ModelProvider(
                    "together_llama32", "meta-llama/Llama-3.2-3B-Instruct-Turbo",
                    "https://api.together.xyz/v1/chat/completions",
                    {"Authorization": f"Bearer {config.get_api_key('together')}"},
                    7, 1000
                ),
                ModelProvider(
                    "together_llama31", "meta-llama/Llama-3.1-8B-Instruct-Turbo",
                    "https://api.together.xyz/v1/chat/completions",
                    {"Authorization": f"Bearer {config.get_api_key('together')}"},
                    8, 1000
                )
            ])
        
        if config.has_api_key('huggingface'):
            providers.append(
                ModelProvider(
                    "huggingface_llama", "meta-llama/Llama-2-7b-chat-hf",
                    "https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
                    {"Authorization": f"Bearer {config.get_api_key('huggingface')}"},
                    9, 10000
                )
            )
        
        if config.has_api_key('openrouter'):
            providers.append(
                ModelProvider(
                    "openrouter_free", "mistralai/mistral-7b-instruct:free",
                    "https://openrouter.ai/api/v1/chat/completions",
                    {"Authorization": f"Bearer {config.get_api_key('openrouter')}"},
                    10, 200
                )
            )
        
        if config.has_api_key('anthropic'):
            providers.append(
                ModelProvider(
                    "anthropic_claude", "claude-3-haiku-20240307",
                    "https://api.anthropic.com/v1/messages",
                    {
                        "x-api-key": config.get_api_key('anthropic'),
                        "anthropic-version": "2023-06-01"
                    },
                    11, 100
                )
            )
        
        if config.has_api_key('cohere'):
            providers.append(
                ModelProvider(
                    "cohere_free", "command-light",
                    "https://api.cohere.ai/v1/chat",
                    {"Authorization": f"Bearer {config.get_api_key('cohere')}"},
                    12, 1000
                )
            )
        
        return sorted(providers, key=lambda p: p.priority)
    
    def _check_ollama(self) -> bool:
        """Check if Ollama is available."""
        try:
            import ollama
            ollama.list()
            return True
        except:
            return False
    
    async def health_check(self):
        """Perform health check on all providers."""
        if time.time() - self.last_health_check < self.health_check_interval:
            return
        
        logger.info("Starting health check for all providers")
        tasks = []
        
        for provider in self.providers:
            if provider.url != "local":
                tasks.append(self._check_provider_health(provider))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        self.last_health_check = time.time()
        logger.info("Health check completed")
    
    @with_timeout(10)
    async def _check_provider_health(self, provider: ModelProvider):
        """Check health of a single provider."""
        try:
            test_messages = [{"role": "user", "content": "Hi"}]
            start_time = time.time()
            
            async with aiohttp.ClientSession() as session:
                payload = self._build_payload(provider, test_messages, 0.1)
                async with session.post(
                    provider.url, 
                    headers=provider.headers, 
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        provider.status = ModelStatus.HEALTHY
                        provider.avg_response_time = time.time() - start_time
                        provider.error_count = 0
                    else:
                        provider.status = ModelStatus.DEGRADED
                        provider.error_count += 1
                        
        except Exception as e:
            provider.status = ModelStatus.FAILED
            provider.error_count += 1
            logger.warning(f"Health check failed for {provider.name}: {e}")
        
        provider.last_check = time.time()
    
    def get_available_providers(self) -> List[ModelProvider]:
        """Get available providers sorted by priority and health."""
        available = []
        
        for provider in self.providers:
            # Check daily limits
            if provider.used_today >= provider.daily_limit:
                continue
                
            # Check health status
            if provider.status == ModelStatus.FAILED:
                continue
                
            available.append(provider)
        
        # Sort by priority, then by health and response time
        return sorted(available, key=lambda p: (
            p.priority,
            p.status != ModelStatus.HEALTHY,
            p.avg_response_time
        ))
    
    @with_retry(max_retries=2)
    async def generate_response(self, messages: List[Dict], temperature: float = 0.95) -> str:
        """Generate response with automatic failover."""
        await self.health_check()
        available_providers = self.get_available_providers()
        
        if not available_providers:
            return await self._emergency_fallback()
        
        # Try providers in parallel (top 3)
        tasks = []
        for provider in available_providers[:3]:
            task = asyncio.create_task(
                self._try_provider(provider, messages, temperature)
            )
            tasks.append((provider, task))
        
        try:
            done, pending = await asyncio.wait(
                [task for _, task in tasks],
                return_when=asyncio.FIRST_COMPLETED,
                timeout=config.model.timeout
            )
            
            # Cancel pending tasks
            for task in pending:
                task.cancel()
            
            # Get first successful result
            for provider, task in tasks:
                if task in done:
                    try:
                        result = await task
                        if result:
                            provider.used_today += 1
                            return result
                    except Exception as e:
                        logger.error(f"Provider {provider.name} failed: {e}")
                        continue
            
        except asyncio.TimeoutError:
            logger.error("All providers timed out")
        
        return await self._emergency_fallback()
    
    @with_timeout(15)
    async def _try_provider(self, provider: ModelProvider, messages: List[Dict], temperature: float) -> Optional[str]:
        """Try a single provider."""
        start_time = time.time()
        
        try:
            if provider.url == "local":
                result = await self._local_request(provider, messages, temperature)
            else:
                result = await self._api_request(provider, messages, temperature)
            
            # Log performance
            duration = time.time() - start_time
            perf_logger.log_request("system", provider.name, duration, bool(result))
            
            return result
            
        except Exception as e:
            duration = time.time() - start_time
            perf_logger.log_request("system", provider.name, duration, False)
            perf_logger.log_error(e, {"provider": provider.name})
            raise
    
    async def _local_request(self, provider: ModelProvider, messages: List[Dict], temperature: float) -> str:
        """Make local Ollama request."""
        import ollama
        
        loop = asyncio.get_event_loop()
        
        def ollama_call():
            response = ollama.chat(
                model=provider.model,
                messages=messages,
                options={
                    'temperature': temperature,
                    'num_predict': config.model.max_tokens
                }
            )
            return response['message']['content'].strip()
        
        return await loop.run_in_executor(None, ollama_call)
    
    async def _api_request(self, provider: ModelProvider, messages: List[Dict], temperature: float) -> str:
        """Make API request to cloud provider."""
        async with aiohttp.ClientSession() as session:
            payload = self._build_payload(provider, messages, temperature)
            
            async with session.post(
                provider.url,
                headers=provider.headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=config.model.timeout)
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._extract_response(provider, data)
                else:
                    raise Exception(f"API error: {response.status}")
    
    def _build_payload(self, provider: ModelProvider, messages: List[Dict], temperature: float) -> Dict:
        """Build request payload for provider."""
        if "anthropic" in provider.name:
            return {
                "model": provider.model,
                "max_tokens": config.model.max_tokens,
                "messages": [msg for msg in messages if msg['role'] != 'system']
            }
        elif "cohere" in provider.name:
            return {
                "message": messages[-1]['content'],
                "model": provider.model,
                "temperature": temperature,
                "max_tokens": config.model.max_tokens
            }
        elif "huggingface" in provider.name:
            return {
                "inputs": messages[-1]['content'],
                "parameters": {
                    "temperature": temperature,
                    "max_length": config.model.max_tokens
                }
            }
        else:
            # Standard OpenAI format
            return {
                "model": provider.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": config.model.max_tokens
            }
    
    def _extract_response(self, provider: ModelProvider, data: Dict) -> str:
        """Extract response text from API response."""
        if "anthropic" in provider.name:
            return data['content'][0]['text']
        elif "cohere" in provider.name:
            return data['text']
        elif "huggingface" in provider.name:
            return data[0]['generated_text']
        else:
            # Standard OpenAI format
            return data['choices'][0]['message']['content']
    
    async def _emergency_fallback(self) -> str:
        """Emergency fallback response."""
        fallbacks = [
            "Arre yaar, all my AI models are acting up right now... 😅 Try again in a moment!",
            "Sorry, having some technical issues. Give me a sec!",
            "Hmm, all models are busy right now. That's unusual! Try again?",
            "Technical difficulties! But I'm still here 💕"
        ]
        import random
        return random.choice(fallbacks)
    
    def get_status(self) -> Dict[str, Any]:
        """Get system status."""
        return {
            "total_providers": len(self.providers),
            "available_providers": len(self.get_available_providers()),
            "providers": [
                {
                    "name": p.name,
                    "status": p.status.value,
                    "used_today": p.used_today,
                    "daily_limit": p.daily_limit,
                    "avg_response_time": p.avg_response_time,
                    "error_count": p.error_count
                }
                for p in self.providers
            ]
        }

# Global instance
llm_system = LLMFallbackSystem()