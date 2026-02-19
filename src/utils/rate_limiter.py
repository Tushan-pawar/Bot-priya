"""Advanced rate limiting with anti-spam detection."""
import time
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, deque
from ..utils.logging import logger

@dataclass
class RateLimit:
    """Rate limit configuration."""
    requests: int
    window: int  # seconds
    burst: int = 0  # burst allowance

@dataclass
class UserLimitState:
    """User rate limit state."""
    requests: deque = field(default_factory=deque)
    last_request: float = 0
    violations: int = 0
    blocked_until: float = 0
    spam_score: float = 0

class AntiSpamDetector:
    """Detects spam patterns."""
    
    def __init__(self):
        self.message_history: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.spam_patterns = [
            lambda msgs: len(msgs) > 5 and len({msg[0] for msg in msgs[-5:]}) == 1,  # Repeated messages
            lambda msgs: len(msgs) > 3 and all(len(msg[0]) < 10 for msg in msgs[-3:]),  # Short spam
            lambda msgs: len(msgs) > 10 and (msgs[-1][1] - msgs[-10][1]) < 30,  # High frequency
        ]
    
    def check_spam(self, user_id: str, message: str) -> float:
        """Check spam score (0.0 = not spam, 1.0 = definitely spam)."""
        now = time.time()
        
        # Clean old messages (last 5 minutes)
        self.message_history[user_id] = [
            (msg, timestamp) for msg, timestamp in self.message_history[user_id]
            if now - timestamp < 300
        ]
        
        # Add current message
        self.message_history[user_id].append((message, now))
        
        # Check patterns
        spam_score = 0.0
        messages = self.message_history[user_id]
        
        for pattern in self.spam_patterns:
            if pattern(messages):
                spam_score += 0.3
        
        # Additional checks
        if len(message) < 3:  # Very short messages
            spam_score += 0.2
        
        if message.isupper() and len(message) > 10:  # ALL CAPS
            spam_score += 0.2
        
        return min(spam_score, 1.0)

class AdvancedRateLimiter:
    """Advanced rate limiting with anti-spam."""
    
    def __init__(self):
        self.user_limits = {
            "default": RateLimit(requests=10, window=60, burst=3),
            "premium": RateLimit(requests=30, window=60, burst=5),
            "admin": RateLimit(requests=100, window=60, burst=10)
        }
        
        self.server_limits = {
            "default": RateLimit(requests=100, window=60),
            "large": RateLimit(requests=300, window=60)
        }
        
        self.user_states: Dict[str, UserLimitState] = defaultdict(UserLimitState)
        self.server_states: Dict[str, UserLimitState] = defaultdict(UserLimitState)
        self.admin_overrides: Dict[str, float] = {}  # user_id -> expiry_time
        self.spam_detector = AntiSpamDetector()
        
        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_task())
    
    async def check_rate_limit(
        self, 
        user_id: str, 
        server_id: Optional[str] = None,
        message: str = "",
        user_tier: str = "default"
    ) -> Tuple[bool, Optional[str]]:
        """Check if request is allowed."""
        now = time.time()
        
        # Check admin override
        if user_id in self.admin_overrides:
            if now < self.admin_overrides[user_id]:
                return True, None
            else:
                del self.admin_overrides[user_id]
        
        # Check spam
        if message:
            spam_score = self.spam_detector.check_spam(user_id, message)
            if spam_score > 0.7:
                logger.warning(f"Spam detected from user {user_id}: score {spam_score}")
                return False, f"Message flagged as spam (score: {spam_score:.2f})"
        
        # Check user rate limit
        user_allowed, user_reason = self._check_user_limit(user_id, user_tier, now)
        if not user_allowed:
            return False, user_reason
        
        # Check server rate limit
        if server_id:
            server_allowed, server_reason = self._check_server_limit(server_id, now)
            if not server_allowed:
                return False, server_reason
        
        # Record successful request
        self._record_request(user_id, server_id, now)
        
        await asyncio.sleep(0)  # Ensure async behavior
        return True, None
    
    def _check_user_limit(self, user_id: str, tier: str, now: float) -> Tuple[bool, Optional[str]]:
        """Check user-specific rate limit."""
        state = self.user_states[user_id]
        limit = self.user_limits.get(tier, self.user_limits["default"])
        
        # Check if user is blocked
        if now < state.blocked_until:
            remaining = int(state.blocked_until - now)
            return False, f"Rate limited. Try again in {remaining} seconds."
        
        # Clean old requests
        while state.requests and now - state.requests[0] > limit.window:
            state.requests.popleft()
        
        # Check limit
        if len(state.requests) >= limit.requests:
            # Check burst allowance
            if limit.burst > 0 and len(state.requests) < limit.requests + limit.burst:
                # Allow burst but increase violation count
                state.violations += 1
                if state.violations > 3:
                    state.blocked_until = now + (60 * state.violations)  # Progressive blocking
                    return False, f"Burst limit exceeded. Blocked for {60 * state.violations} seconds."
            else:
                return False, f"Rate limit exceeded. Max {limit.requests} requests per {limit.window} seconds."
        
        return True, None
    
    def _check_server_limit(self, server_id: str, now: float) -> Tuple[bool, Optional[str]]:
        """Check server-wide rate limit."""
        state = self.server_states[server_id]
        limit = self.server_limits["default"]  # Could be configurable per server
        
        # Clean old requests
        while state.requests and now - state.requests[0] > limit.window:
            state.requests.popleft()
        
        # Check limit
        if len(state.requests) >= limit.requests:
            return False, "Server rate limit exceeded. Try again later."
        
        return True, None
    
    def _record_request(self, user_id: str, server_id: Optional[str], now: float):
        """Record successful request."""
        self.user_states[user_id].requests.append(now)
        self.user_states[user_id].last_request = now
        
        if server_id:
            self.server_states[server_id].requests.append(now)
    
    def add_admin_override(self, user_id: str, duration: int = 3600):
        """Add admin override for user."""
        self.admin_overrides[user_id] = time.time() + duration
        logger.info(f"Admin override added for user {user_id} for {duration} seconds")
    
    def reset_user_limits(self, user_id: str):
        """Reset limits for user."""
        if user_id in self.user_states:
            del self.user_states[user_id]
        logger.info(f"Rate limits reset for user {user_id}")
    
    def get_user_status(self, user_id: str) -> Dict[str, any]:
        """Get user rate limit status."""
        state = self.user_states.get(user_id)
        if not state:
            return {"requests": 0, "violations": 0, "blocked": False}
        
        now = time.time()
        return {
            "requests": len(state.requests),
            "violations": state.violations,
            "blocked": now < state.blocked_until,
            "blocked_until": state.blocked_until if now < state.blocked_until else None,
            "last_request": state.last_request
        }
    
    async def _cleanup_task(self):
        """Cleanup old state data."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                now = time.time()
                
                # Clean user states
                to_remove = []
                for user_id, state in self.user_states.items():
                    if now - state.last_request > 3600:  # 1 hour inactive
                        to_remove.append(user_id)
                
                for user_id in to_remove:
                    del self.user_states[user_id]
                
                # Clean admin overrides
                expired_overrides = [
                    user_id for user_id, expiry in self.admin_overrides.items()
                    if now > expiry
                ]
                for user_id in expired_overrides:
                    del self.admin_overrides[user_id]
                
                if to_remove or expired_overrides:
                    logger.info(f"Cleaned up {len(to_remove)} user states and {len(expired_overrides)} admin overrides")
                    
            except Exception as e:
                logger.error(f"Rate limiter cleanup error: {e}")

# Global instance
rate_limiter = AdvancedRateLimiter()