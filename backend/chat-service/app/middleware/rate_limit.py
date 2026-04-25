from collections import defaultdict
from datetime import datetime, timedelta
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import settings
from app.core.logging import logger
from typing import Dict, Tuple


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware.
    In production, use Redis-based rate limiting for distributed systems.
    """
    
    def __init__(self, app, requests_per_minute: int = None):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_MESSAGES_PER_MINUTE
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = timedelta(minutes=5)
        self.last_cleanup = datetime.utcnow()
    
    async def dispatch(self, request: Request, call_next):
        # Only rate limit message sending endpoints
        if request.url.path.endswith("/messages") and request.method == "POST":
            user_id = request.state.get("user_id")
            if user_id:
                if not self._check_rate_limit(str(user_id)):
                    logger.warning(f"Rate limit exceeded for user {user_id}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail="Rate limit exceeded. Please try again later."
                    )
        
        response = await call_next(request)
        return response
    
    def _check_rate_limit(self, user_id: str) -> bool:
        """Check if user has exceeded rate limit."""
        now = datetime.utcnow()
        
        # Cleanup old entries periodically
        if (now - self.last_cleanup) > self.cleanup_interval:
            self._cleanup_old_entries(now)
            self.last_cleanup = now
        
        # Get user's requests in the last minute
        user_requests = self.requests[user_id]
        cutoff_time = now - timedelta(minutes=1)
        recent_requests = [req_time for req_time in user_requests if req_time > cutoff_time]
        
        # Update requests list
        self.requests[user_id] = recent_requests
        
        # Check limit
        if len(recent_requests) >= self.requests_per_minute:
            return False
        
        # Add current request
        recent_requests.append(now)
        self.requests[user_id] = recent_requests
        return True
    
    def _cleanup_old_entries(self, now: datetime):
        """Remove entries older than 1 minute."""
        cutoff_time = now - timedelta(minutes=1)
        for user_id in list(self.requests.keys()):
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id]
                if req_time > cutoff_time
            ]
            if not self.requests[user_id]:
                del self.requests[user_id]
