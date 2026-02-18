"""Concurrency control and timeout handling."""
import asyncio
import time
from typing import Dict, Any, Optional, Callable, TypeVar, Awaitable
from contextlib import asynccontextmanager
from functools import wraps
from ..utils.logging import logger

T = TypeVar('T')

class ConcurrencyManager:
    """Manages concurrent operations with limits and timeouts."""
    
    def __init__(self, max_concurrent: int = 10):
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests = {}
        self.voice_lock = asyncio.Lock()
        self.voice_user = None
        
    @asynccontextmanager
    async def request_slot(self, user_id: str, operation: str):
        """Acquire a request slot with concurrency control."""
        async with self.semaphore:
            request_id = f"{user_id}_{operation}_{time.time()}"
            self.active_requests[request_id] = {
                'user_id': user_id,
                'operation': operation,
                'start_time': time.time()
            }
            
            try:
                yield request_id
            finally:
                self.active_requests.pop(request_id, None)
    
    @asynccontextmanager
    async def voice_exclusive(self, user_id: str, timeout: int = 30):
        """Exclusive voice channel access."""
        try:
            await asyncio.wait_for(self.voice_lock.acquire(), timeout=timeout)
            if self.voice_user and self.voice_user != user_id:
                raise RuntimeError(f"Voice channel busy with user {self.voice_user}")
            
            self.voice_user = user_id
            logger.info(f"Voice lock acquired by {user_id}")
            yield
            
        except asyncio.TimeoutError:
            raise RuntimeError("Voice channel lock timeout")
        finally:
            self.voice_user = None
            if self.voice_lock.locked():
                self.voice_lock.release()
            logger.info(f"Voice lock released by {user_id}")
    
    def get_active_requests(self) -> Dict[str, Any]:
        """Get currently active requests."""
        return self.active_requests.copy()

def with_timeout(timeout: int):
    """Decorator for adding timeout to async functions."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=timeout)
            except asyncio.TimeoutError:
                logger.error(f"Function {func.__name__} timed out after {timeout}s")
                raise
        return wrapper
    return decorator

def with_retry(max_retries: int = 3, delay: float = 1.0):
    """Decorator for adding retry logic to async functions."""
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {e}")
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            
            raise last_exception
        return wrapper
    return decorator

class MemoryManager:
    """Memory usage monitoring and cleanup."""
    
    def __init__(self, max_memory_mb: int = 500):
        self.max_memory_mb = max_memory_mb
        self.cleanup_callbacks = []
        
    def register_cleanup(self, callback: Callable[[], None]):
        """Register cleanup callback."""
        self.cleanup_callbacks.append(callback)
    
    async def check_memory(self):
        """Check memory usage and cleanup if needed."""
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                logger.warning(f"Memory usage {memory_mb:.1f}MB exceeds limit {self.max_memory_mb}MB")
                await self.cleanup()
                
        except ImportError:
            logger.warning("psutil not available for memory monitoring")
    
    async def cleanup(self):
        """Run cleanup callbacks."""
        for callback in self.cleanup_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
            except Exception as e:
                logger.error(f"Cleanup callback failed: {e}")

# Global instances
concurrency_manager = ConcurrencyManager()
memory_manager = MemoryManager()