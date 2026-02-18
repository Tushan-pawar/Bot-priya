"""Helper utilities for common operations."""
import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Callable, TypeVar
from pathlib import Path
from datetime import datetime, timedelta

T = TypeVar('T')

def safe_json_load(file_path: Path, default: Any = None) -> Any:
    """Safely load JSON file with fallback."""
    try:
        if file_path.exists():
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return default or {}

def safe_json_save(file_path: Path, data: Any) -> bool:
    """Safely save JSON file with atomic write."""
    try:
        # Ensure parent directory exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Atomic write using temporary file
        temp_file = file_path.with_suffix('.tmp')
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        temp_file.replace(file_path)
        return True
    except Exception:
        return False

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def format_duration(seconds: float) -> str:
    """Format duration in human-readable format."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}m {secs}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def get_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()

def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """Parse ISO timestamp string."""
    try:
        return datetime.fromisoformat(timestamp)
    except (ValueError, TypeError):
        return None

def is_recent(timestamp: str, max_age_minutes: int = 30) -> bool:
    """Check if timestamp is recent."""
    dt = parse_timestamp(timestamp)
    if not dt:
        return False
    
    age = datetime.now() - dt
    return age < timedelta(minutes=max_age_minutes)

def clean_text(text: str) -> str:
    """Clean text for processing."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = ' '.join(text.split())
    
    # Remove control characters
    text = ''.join(char for char in text if ord(char) >= 32 or char in '\n\t')
    
    return text.strip()

def extract_mentions(text: str) -> List[str]:
    """Extract user mentions from text."""
    import re
    pattern = r'<@!?(\d+)>'
    return re.findall(pattern, text)

def remove_mentions(text: str) -> str:
    """Remove user mentions from text."""
    import re
    pattern = r'<@!?\d+>'
    return re.sub(pattern, '', text).strip()

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity (simple implementation)."""
    if not text1 or not text2:
        return 0.0
    
    words1 = set(text1.lower().split())
    words2 = set(text2.lower().split())
    
    if not words1 or not words2:
        return 0.0
    
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    return len(intersection) / len(union)

class RateLimiter:
    """Simple rate limiter."""
    
    def __init__(self, max_requests: int, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, List[float]] = {}
    
    def is_allowed(self, key: str) -> bool:
        """Check if request is allowed."""
        now = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Clean old requests
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.time_window
        ]
        
        # Check limit
        if len(self.requests[key]) >= self.max_requests:
            return False
        
        # Add current request
        self.requests[key].append(now)
        return True
    
    def get_remaining(self, key: str) -> int:
        """Get remaining requests for key."""
        if key not in self.requests:
            return self.max_requests
        
        now = time.time()
        recent_requests = [
            req_time for req_time in self.requests[key]
            if now - req_time < self.time_window
        ]
        
        return max(0, self.max_requests - len(recent_requests))

class CircuitBreaker:
    """Circuit breaker for fault tolerance."""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = 0
        self.state = "closed"  # closed, open, half-open
    
    def call(self, func: Callable[[], T]) -> Optional[T]:
        """Call function with circuit breaker protection."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                return None
        
        try:
            result = func()
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            return None
    
    async def acall(self, func: Callable[[], T]) -> Optional[T]:
        """Async version of call."""
        if self.state == "open":
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "half-open"
            else:
                return None
        
        try:
            result = await func()
            if self.state == "half-open":
                self.state = "closed"
                self.failure_count = 0
            return result
        except Exception:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "open"
            
            return None