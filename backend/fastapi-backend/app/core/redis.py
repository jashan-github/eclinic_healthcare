"""
Redis client for caching and rate limiting
Handles connection pooling and common operations
"""

from typing import Optional, Any
import json
import redis
from redis import ConnectionPool, Redis
from loguru import logger

from app.core.config import settings


class RedisClient:
    """Redis client wrapper with connection pooling"""
    
    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[Redis] = None
    
    def connect(self):
        """Initialize Redis connection pool"""
        if not settings.REDIS_ENABLED:
            logger.warning("Redis is disabled in configuration")
            return
        
        try:
            self._pool = ConnectionPool.from_url(
                settings.REDIS_URL,
                decode_responses=True,
                max_connections=50
            )
            self._client = Redis(connection_pool=self._pool)
            
            # Test connection
            self._client.ping()
            logger.info(f"Redis connected: {settings.REDIS_URL}")
        
        except Exception as e:
            logger.error(f"Redis connection failed: {str(e)}")
            self._client = None
    
    def disconnect(self):
        """Close Redis connection"""
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis disconnected")
    
    @property
    def client(self) -> Optional[Redis]:
        """Get Redis client instance"""
        if not settings.REDIS_ENABLED:
            return None
        
        if self._client is None:
            self.connect()
        
        return self._client
    
    def is_available(self) -> bool:
        """Check if Redis is available"""
        if not settings.REDIS_ENABLED:
            return False
        
        try:
            if self.client:
                self.client.ping()
                return True
        except Exception as e:
            logger.warning(f"Redis unavailable: {str(e)}")
        
        return False
    
    # Cache operations
    
    def get(self, key: str) -> Optional[str]:
        """Get value from cache"""
        if not self.client:
            return None
        
        try:
            return self.client.get(key)
        except Exception as e:
            logger.error(f"Redis GET error: {str(e)}")
            return None
    
    def set(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            expire: Expiration in seconds
        """
        if not self.client:
            return False
        
        try:
            if expire:
                return bool(self.client.setex(key, expire, value))
            else:
                return bool(self.client.set(key, value))
        except Exception as e:
            logger.error(f"Redis SET error: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.delete(key))
        except Exception as e:
            logger.error(f"Redis DELETE error: {str(e)}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists"""
        if not self.client:
            return False
        
        try:
            return bool(self.client.exists(key))
        except Exception as e:
            logger.error(f"Redis EXISTS error: {str(e)}")
            return False
    
    # JSON operations
    
    def get_json(self, key: str) -> Optional[Any]:
        """Get JSON value from cache"""
        value = self.get(key)
        if value:
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                logger.error(f"Failed to decode JSON for key: {key}")
        return None
    
    def set_json(
        self,
        key: str,
        value: Any,
        expire: Optional[int] = None
    ) -> bool:
        """Set JSON value in cache"""
        try:
            json_value = json.dumps(value)
            return self.set(key, json_value, expire)
        except (TypeError, json.JSONDecodeError) as e:
            logger.error(f"Failed to encode JSON: {str(e)}")
            return False
    
    # Rate limiting operations
    
    def increment(self, key: str, expire: Optional[int] = None) -> Optional[int]:
        """
        Increment counter
        
        Args:
            key: Counter key
            expire: Set expiration on first increment
        
        Returns:
            Current counter value or None on error
        """
        if not self.client:
            return None
        
        try:
            # Use pipeline for atomic operations
            pipe = self.client.pipeline()
            pipe.incr(key)
            
            # Set expiration only if key is new
            if expire and not self.client.exists(key):
                pipe.expire(key, expire)
            
            results = pipe.execute()
            return results[0]
        
        except Exception as e:
            logger.error(f"Redis INCR error: {str(e)}")
            return None
    
    def get_ttl(self, key: str) -> Optional[int]:
        """
        Get time-to-live for key
        
        Returns:
            TTL in seconds, -1 if no expiration, -2 if key doesn't exist
        """
        if not self.client:
            return None
        
        try:
            return self.client.ttl(key)
        except Exception as e:
            logger.error(f"Redis TTL error: {str(e)}")
            return None
    
    def check_rate_limit(
        self,
        key: str,
        limit: int,
        window: int
    ) -> tuple[bool, int, int]:
        """
        Check if rate limit is exceeded
        
        Args:
            key: Rate limit key (e.g., "rate_limit:ip:192.168.1.1")
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            Tuple of (allowed, current_count, retry_after)
        """
        if not self.client:
            # If Redis unavailable, allow request (fail open)
            return (True, 0, 0)
        
        try:
            # Get current count
            current = self.client.get(key)
            
            if current is None:
                # First request in window
                self.client.setex(key, window, 1)
                return (True, 1, 0)
            
            current_count = int(current)
            
            if current_count >= limit:
                # Rate limit exceeded
                ttl = self.client.ttl(key)
                retry_after = ttl if ttl > 0 else window
                return (False, current_count, retry_after)
            
            # Increment counter
            new_count = self.client.incr(key)
            return (True, new_count, 0)
        
        except Exception as e:
            logger.error(f"Rate limit check error: {str(e)}")
            # Fail open on error
            return (True, 0, 0)
    
    # Session operations
    
    def set_session(
        self,
        session_id: str,
        data: dict,
        expire: int = 3600
    ) -> bool:
        """Set session data"""
        return self.set_json(f"session:{session_id}", data, expire)
    
    def get_session(self, session_id: str) -> Optional[dict]:
        """Get session data"""
        return self.get_json(f"session:{session_id}")
    
    def delete_session(self, session_id: str) -> bool:
        """Delete session"""
        return self.delete(f"session:{session_id}")
    
    # Token blacklist operations (for JWT revocation)
    
    def blacklist_token(self, token_jti: str, expire: int) -> bool:
        """
        Add token to blacklist
        
        Args:
            token_jti: JWT ID (jti claim)
            expire: Token expiration time in seconds
        """
        return self.set(f"blacklist:{token_jti}", "1", expire)
    
    def is_token_blacklisted(self, token_jti: str) -> bool:
        """Check if token is blacklisted"""
        return self.exists(f"blacklist:{token_jti}")


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> RedisClient:
    """Get Redis client (for dependency injection)"""
    return redis_client
