"""
Redis Pub/Sub service for video session waiting room notifications
Uses Redis PUB/SUB to broadcast waiting room status across multiple instances
"""

import json
import asyncio
from typing import Callable, Optional, Dict, Any
from uuid import UUID
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from app.core.config import settings
from loguru import logger


class VideoSessionRedisService:
    """Redis Pub/Sub service for video session waiting room notifications"""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self._connected = False
    
    async def connect(self, retry_count: int = 3, retry_delay: float = 2.0):
        """Connect to Redis with retry logic"""
        if not settings.REDIS_ENABLED:
            logger.warning("Redis is disabled - PUB/SUB will not work")
            return
        
        for attempt in range(retry_count):
            try:
                self.redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                await self.redis_client.ping()
                self._connected = True
                logger.info("Video Session Redis PUB/SUB connected")
                return
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1}/{retry_count} failed: {e}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis after {retry_count} attempts: {e}")
                    self._connected = False
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.aclose()
            self.pubsub = None
        
        if self.redis_client:
            await self.redis_client.aclose()
            self._connected = False
            logger.info("Video Session Redis PUB/SUB disconnected")
    
    def _get_channel_name(self, session_id: UUID) -> str:
        """Get Redis channel name for a video session"""
        return f"video_session:{str(session_id)}"
    
    async def publish_waiting_room_event(
        self,
        session_id: UUID,
        event_type: str,
        data: Dict[str, Any]
    ):
        """
        Publish waiting room event to Redis channel
        
        Args:
            session_id: Video session ID
            event_type: Event type (e.g., "doctor_joined", "session_ready")
            data: Event data
        """
        if not settings.REDIS_ENABLED or not self._connected:
            if not self._connected:
                await self.connect()
            if not self._connected:
                logger.warning("Redis not available - event not published")
                return
        
        channel = self._get_channel_name(session_id)
        message = {
            "type": event_type,
            "session_id": str(session_id),
            "data": data,
            "timestamp": asyncio.get_event_loop().time()
        }
        
        try:
            await self.redis_client.publish(
                channel,
                json.dumps(message, default=str)
            )
            logger.debug(f"Published {event_type} event to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish event to Redis: {e}")
    
    async def subscribe_to_session(
        self,
        session_id: UUID,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to a video session channel and process messages
        
        Args:
            session_id: Video session ID
            callback: Async function to call with each message
        """
        if not settings.REDIS_ENABLED:
            logger.warning("Redis is disabled - subscription will not work")
            return
        
        if not self._connected:
            await self.connect()
        
        if not self._connected:
            logger.error("Cannot subscribe - Redis not available")
            return
        
        channel = self._get_channel_name(session_id)
        self.pubsub = self.redis_client.pubsub()
        
        try:
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to video session channel {channel}")
            
            async for message in self.pubsub.listen():
                if message["type"] == "message":
                    try:
                        data = json.loads(message["data"])
                        await callback(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse Redis message: {e}")
                    except Exception as e:
                        logger.error(f"Error in Redis callback: {e}")
        except asyncio.CancelledError:
            logger.info(f"Unsubscribing from channel {channel}")
            await self.pubsub.unsubscribe(channel)
            raise
        except Exception as e:
            logger.error(f"Error in Redis subscription: {e}")
            raise


# Global Redis service instance
video_session_redis_service = VideoSessionRedisService()
