"""
Rate limiting middleware
Implements per-IP and per-user rate limiting using Redis
"""

from typing import Callable, Optional, Union, Tuple
from uuid import UUID
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.core.config import settings
from app.core.redis import redis_client
from app.core.exceptions import RateLimitException


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware with Redis backend
    Supports both IP-based and user-based rate limiting
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.per_minute = settings.RATE_LIMIT_PER_MINUTE
        # Parse allowed origins for CORS headers on rate limit responses
        self._allowed_origins = set()
        if isinstance(settings.CORS_ORIGINS, str):
            self._allowed_origins = {
                origin.strip().rstrip('/') 
                for origin in settings.CORS_ORIGINS.split(",") 
                if origin.strip()
            }
    
    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """
        Add CORS headers to response to prevent browser CORS errors on rate limit
        
        Args:
            response: Response object to add headers to
            request: Request object to get origin from
        """
        origin = request.headers.get("origin")
        if origin:
            origin_normalized = origin.rstrip('/')
            # Check if origin is allowed
            is_allowed = origin_normalized in self._allowed_origins
            
            # In development, also allow localhost origins
            if not is_allowed and settings.is_development:
                origin_lower = origin_normalized.lower()
                if (origin_lower.startswith("http://localhost") or 
                    origin_lower.startswith("http://127.0.0.1") or
                    origin_lower.startswith("https://localhost") or
                    origin_lower.startswith("https://127.0.0.1")):
                    is_allowed = True
            
            if is_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                if settings.CORS_ALLOW_CREDENTIALS:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Expose-Headers"] = (
                    "X-Request-ID, X-Process-Time, X-RateLimit-Limit, "
                    "X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After"
                )
        # Parse allowed origins for CORS headers on rate limit responses
        self._allowed_origins = set()
        if isinstance(settings.CORS_ORIGINS, str):
            self._allowed_origins = {
                origin.strip().rstrip('/') 
                for origin in settings.CORS_ORIGINS.split(",") 
                if origin.strip()
            }
    
    def _add_cors_headers(self, response: Response, request: Request) -> None:
        """
        Add CORS headers to response to prevent browser CORS errors on rate limit
        
        Args:
            response: Response object to add headers to
            request: Request object to get origin from
        """
        origin = request.headers.get("origin")
        if origin:
            origin_normalized = origin.rstrip('/')
            # Check if origin is allowed
            is_allowed = origin_normalized in self._allowed_origins
            
            # In development, also allow localhost origins
            if not is_allowed and settings.is_development:
                origin_lower = origin_normalized.lower()
                if (origin_lower.startswith("http://localhost") or 
                    origin_lower.startswith("http://127.0.0.1") or
                    origin_lower.startswith("https://localhost") or
                    origin_lower.startswith("https://127.0.0.1")):
                    is_allowed = True
            
            if is_allowed:
                response.headers["Access-Control-Allow-Origin"] = origin
                if settings.CORS_ALLOW_CREDENTIALS:
                    response.headers["Access-Control-Allow-Credentials"] = "true"
                response.headers["Access-Control-Expose-Headers"] = (
                    "X-Request-ID, X-Process-Time, X-RateLimit-Limit, "
                    "X-RateLimit-Remaining, X-RateLimit-Reset, Retry-After"
                )
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting"""
        
        if not self.enabled:
            return await call_next(request)
        
        # Skip rate limiting for health checks and preflight requests
        # Skip rate limiting for health checks and preflight requests
        if request.url.path in ["/health", "/", "/docs", "/redoc", "/openapi.json"]:
            return await call_next(request)
        
        # Skip rate limiting for OPTIONS (CORS preflight) requests
        if request.method == "OPTIONS":
            return await call_next(request)
        
        # Get user ID if authenticated
        user_id = getattr(request.state, "user_id", None)
        
        # For authenticated users, skip IP-based rate limiting and only use user-based
        # This prevents issues with shared IPs (NAT, proxies, etc.)
        # For unauthenticated users, apply IP-based rate limiting
        if not user_id:
            # Get client identifier for IP-based rate limiting (unauthenticated only)
            client_ip = self._get_client_ip(request)
            
            # Check IP-based rate limit (only for unauthenticated users)
            ip_allowed, ip_count, ip_retry = self._check_ip_rate_limit(client_ip)
            
            if not ip_allowed:
                logger.warning(
                    f"IP rate limit exceeded: {client_ip} - "
                    f"{ip_count} requests, retry after {ip_retry}s"
                )
                
                # Add rate limit headers and CORS headers
                response = Response(
                    content='{"success": false, "message": "Too many requests", '
                            '"errors": {"rate_limit": ["Rate limit exceeded"]}, "data": null}',
                    status_code=429,
                    media_type="application/json"
                )
                response.headers["X-RateLimit-Limit"] = str(self.per_minute)
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(ip_retry)
                response.headers["Retry-After"] = str(ip_retry)
                # Add CORS headers to prevent browser CORS errors
                self._add_cors_headers(response, request)
                return response
        
        # Check user-based rate limit (if authenticated)
        if user_id:
            user_allowed, user_count, user_retry = self._check_user_rate_limit(user_id)
            
            if not user_allowed:
                logger.warning(
                    f"User rate limit exceeded: user_id={user_id} - "
                    f"{user_count} requests, retry after {user_retry}s"
                )
                
                response = Response(
                    content='{"success": false, "message": "Too many requests", '
                            '"errors": {"rate_limit": ["Rate limit exceeded"]}, "data": null}',
                    status_code=429,
                    media_type="application/json"
                )
                response.headers["X-RateLimit-Limit"] = str(self.per_minute * 2)  # Higher limit for users
                response.headers["X-RateLimit-Remaining"] = "0"
                response.headers["X-RateLimit-Reset"] = str(user_retry)
                response.headers["Retry-After"] = str(user_retry)
                # Add CORS headers to prevent browser CORS errors
                self._add_cors_headers(response, request)
                # Add CORS headers to prevent browser CORS errors
                self._add_cors_headers(response, request)
                return response
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        if user_id:
            # For authenticated users, show user-based rate limit info
            user_allowed, user_count, _ = self._check_user_rate_limit(user_id)
            remaining = (self.per_minute * 2) - user_count
            response.headers["X-RateLimit-Limit"] = str(self.per_minute * 2)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        else:
            # For unauthenticated users, show IP-based rate limit info
            client_ip = self._get_client_ip(request)
            _, ip_count, _ = self._check_ip_rate_limit(client_ip)
            remaining = self.per_minute - ip_count
            response.headers["X-RateLimit-Limit"] = str(self.per_minute)
            response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address (considering proxies)
        """
        # Check X-Forwarded-For header (if behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get first IP (client IP)
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_ip_rate_limit(self, client_ip: str) -> tuple[bool, int, int]:
        """
        Check IP-based rate limit
        
        Args:
            client_ip: Client IP address
        
        Returns:
            Tuple of (allowed, current_count, retry_after)
        """
        key = f"rate_limit:ip:{client_ip}"
        return redis_client.check_rate_limit(
            key=key,
            limit=self.per_minute,
            window=60  # 1 minute window
        )
    
    def _check_user_rate_limit(self, user_id: Union[str, UUID]) -> tuple[bool, int, int]:
        """
        Check user-based rate limit (higher limit for authenticated users)
        
        Args:
            user_id: User ID
        
        Returns:
            Tuple of (allowed, current_count, retry_after)
        """
        key = f"rate_limit:user:{user_id}"
        # Authenticated users get 2x the limit
        return redis_client.check_rate_limit(
            key=key,
            limit=self.per_minute * 2,
            window=60  # 1 minute window
        )


class EndpointRateLimiter:
    """
    Decorator for endpoint-specific rate limiting
    Can be used as a dependency in routes
    """
    
    def __init__(self, limit: int, window: int = 60):
        """
        Args:
            limit: Maximum requests allowed
            window: Time window in seconds
        """
        self.limit = limit
        self.window = window
    
    async def __call__(self, request: Request):
        """Check rate limit for specific endpoint"""
        
        if not settings.RATE_LIMIT_ENABLED:
            return
        
        # Get user ID or IP
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            key = f"rate_limit:endpoint:{request.url.path}:user:{user_id}"
        else:
            client_ip = self._get_client_ip(request)
            key = f"rate_limit:endpoint:{request.url.path}:ip:{client_ip}"
        
        # Check rate limit
        allowed, count, retry_after = redis_client.check_rate_limit(
            key=key,
            limit=self.limit,
            window=self.window
        )
        
        if not allowed:
            logger.warning(
                f"Endpoint rate limit exceeded: {request.url.path} - "
                f"{count} requests, retry after {retry_after}s"
            )
            raise RateLimitException(retry_after=retry_after)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"


# Predefined rate limiters for common use cases
rate_limit_strict = EndpointRateLimiter(limit=10, window=60)  # 10 req/min
rate_limit_moderate = EndpointRateLimiter(limit=30, window=60)  # 30 req/min
rate_limit_relaxed = EndpointRateLimiter(limit=100, window=60)  # 100 req/min
