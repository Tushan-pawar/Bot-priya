"""Model hot-swapping with health checks and fallback."""
import asyncio
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from ..utils.logging import logger

@dataclass
class ModelInfo:
    """Model information."""
    name: str
    provider: str
    status: str = "unknown"  # unknown, healthy, degraded, failed
    last_check: float = 0
    response_time: float = 0
    error_count: int = 0
    success_count: int = 0

class ModelHotSwapper:
    """Manages dynamic model switching with health checks."""
    
    def __init__(self):
        self.available_models: Dict[str, ModelInfo] = {}
        self.current_model = None
        self.fallback_models: List[str] = []
        self.health_check_interval = 300  # 5 minutes
        self.switching_in_progress = False
        
        # Initialize with default models
        self._initialize_models()
        
        # Start health check task
        asyncio.create_task(self._health_check_loop())
    
    def _initialize_models(self):
        """Initialize available models."""
        # Ollama models
        ollama_models = ["llama3.2", "llama3.1", "mistral", "codellama", "phi3"]
        for model in ollama_models:
            self.available_models[f"ollama_{model}"] = ModelInfo(
                name=model,
                provider="ollama"
            )
        
        # Set default model and fallbacks
        self.current_model = "ollama_llama3.2"
        self.fallback_models = ["ollama_llama3.1", "ollama_mistral"]
    
    async def switch_model(self, model_name: str, force: bool = False) -> bool:
        """Switch to a different model."""
        if self.switching_in_progress and not force:
            logger.warning("Model switch already in progress")
            return False
        
        if model_name not in self.available_models:
            logger.error(f"Model {model_name} not available")
            return False
        
        if model_name == self.current_model:
            logger.info(f"Already using model {model_name}")
            return True
        
        self.switching_in_progress = True
        
        try:
            # Health check new model
            logger.info(f"Switching to model {model_name}...")
            
            if not force:
                health_ok = await self._check_model_health(model_name)
                if not health_ok:
                    logger.error(f"Model {model_name} failed health check")
                    return False
            
            # Switch model
            old_model = self.current_model
            self.current_model = model_name
            
            # Test the switch with a simple query
            if not force:
                test_ok = await self._test_model_switch()
                if not test_ok:
                    logger.error(f"Model {model_name} failed test query, reverting...")
                    self.current_model = old_model
                    return False
            
            logger.info(f"Successfully switched from {old_model} to {model_name}")
            return True
            
        except Exception as e:
            logger.error(f"Model switch failed: {e}")
            return False
        
        finally:
            self.switching_in_progress = False
    
    async def _check_model_health(self, model_name: str) -> bool:
        """Check if model is healthy."""
        model_info = self.available_models[model_name]
        
        try:
            start_time = time.time()
            
            if model_info.provider == "ollama":
                health_ok = await self._check_ollama_model(model_info.name)
            else:
                # For API models, use existing health check
                health_ok = True  # Simplified for now
            
            response_time = time.time() - start_time
            
            if health_ok:
                model_info.status = "healthy"
                model_info.response_time = response_time
                model_info.success_count += 1
                model_info.error_count = max(0, model_info.error_count - 1)  # Decay errors
            else:
                model_info.status = "failed"
                model_info.error_count += 1
            
            model_info.last_check = time.time()
            return health_ok
            
        except Exception as e:
            logger.error(f"Health check failed for {model_name}: {e}")
            model_info.status = "failed"
            model_info.error_count += 1
            model_info.last_check = time.time()
            return False
    
    async def _check_ollama_model(self, model_name: str) -> bool:
        """Check Ollama model health."""
        try:
            import ollama
            
            # Try to list models first
            models = ollama.list()
            model_names = [model['name'].split(':')[0] for model in models['models']]
            
            if model_name not in model_names:
                logger.warning(f"Ollama model {model_name} not found, attempting to pull...")
                try:
                    ollama.pull(model_name)
                    logger.info(f"Successfully pulled model {model_name}")
                except Exception as e:
                    logger.error(f"Failed to pull model {model_name}: {e}")
                    return False
            
            # Test with simple query
            response = ollama.chat(
                model=model_name,
                messages=[{"role": "user", "content": "Hello"}],
                options={"num_predict": 10}
            )
            
            return bool(response and response.get('message', {}).get('content'))
            
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False
    
    async def _test_model_switch(self) -> bool:
        """Test model switch with simple query."""
        try:
            from ..models.llm_fallback import llm_system
            
            # Force use current model for test
            test_messages = [{"role": "user", "content": "Test"}]
            response = await llm_system.generate_response(test_messages, temperature=0.1)
            
            return bool(response and len(response.strip()) > 0)
            
        except Exception as e:
            logger.error(f"Model test failed: {e}")
            return False
    
    async def auto_fallback(self) -> bool:
        """Automatically fallback to healthy model."""
        if not self.fallback_models:
            logger.error("No fallback models configured")
            return False
        
        logger.info("Attempting automatic fallback...")
        
        for fallback_model in self.fallback_models:
            if fallback_model == self.current_model:
                continue
            
            logger.info(f"Trying fallback model: {fallback_model}")
            
            if await self.switch_model(fallback_model):
                logger.info(f"Successfully fell back to {fallback_model}")
                return True
        
        logger.error("All fallback models failed")
        return False
    
    async def _health_check_loop(self):
        """Background health check loop."""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                
                # Check current model health
                if self.current_model:
                    current_healthy = await self._check_model_health(self.current_model)
                    
                    if not current_healthy:
                        logger.warning(f"Current model {self.current_model} is unhealthy")
                        
                        # Try auto-fallback if model has too many errors
                        model_info = self.available_models[self.current_model]
                        if model_info.error_count > 3:
                            logger.warning(f"Model {self.current_model} has {model_info.error_count} errors, attempting fallback")
                            await self.auto_fallback()
                
                # Check fallback models periodically
                for model_name in self.fallback_models:
                    if model_name != self.current_model:
                        await self._check_model_health(model_name)
                
            except Exception as e:
                logger.error(f"Health check loop error: {e}")
    
    def get_model_status(self) -> Dict[str, Any]:
        """Get status of all models."""
        return {
            "current_model": self.current_model,
            "switching_in_progress": self.switching_in_progress,
            "models": {
                name: {
                    "name": info.name,
                    "provider": info.provider,
                    "status": info.status,
                    "last_check": info.last_check,
                    "response_time": info.response_time,
                    "error_count": info.error_count,
                    "success_count": info.success_count,
                    "success_rate": info.success_count / max(1, info.success_count + info.error_count)
                }
                for name, info in self.available_models.items()
            }
        }
    
    def add_model(self, model_name: str, provider: str, model_id: str):
        """Add a new model to the registry."""
        full_name = f"{provider}_{model_name}"
        self.available_models[full_name] = ModelInfo(
            name=model_id,
            provider=provider
        )
        logger.info(f"Added model: {full_name}")
    
    def set_fallback_models(self, models: List[str]):
        """Set fallback model list."""
        valid_models = [m for m in models if m in self.available_models]
        self.fallback_models = valid_models
        logger.info(f"Set fallback models: {valid_models}")

# Global instance
model_swapper = ModelHotSwapper()