import json
import asyncio
from typing import Callable, Optional, Dict, Any
from uuid import UUID
from redis.asyncio import Redis
from redis.asyncio.client import PubSub
from app.core.config import settings
from app.core.logging import logger


class RedisService:
    """Redis Pub/Sub service for chat message broadcasting."""
    
    def __init__(self):
        self.redis_client: Optional[Redis] = None
        self.pubsub: Optional[PubSub] = None
        self._connected = False
    
    async def connect(self, retry_count: int = 3, retry_delay: float = 2.0):
        """Connect to Redis with retry logic."""
        for attempt in range(retry_count):
            try:
                self.redis_client = Redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True,
                    socket_connect_timeout=5,  # 5 second connection timeout
                    socket_timeout=5  # 5 second socket timeout
                )
                await self.redis_client.ping()
                self._connected = True
                logger.info("Connected to Redis")
                return
            except Exception as e:
                if attempt < retry_count - 1:
                    logger.warning(f"Redis connection attempt {attempt + 1}/{retry_count} failed: {e}. Retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"Failed to connect to Redis after {retry_count} attempts: {e}")
                    raise
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.pubsub:
            await self.pubsub.unsubscribe()
            await self.pubsub.aclose()
            self.pubsub = None
        
        if self.redis_client:
            await self.redis_client.aclose()
            self._connected = False
            logger.info("Disconnected from Redis")
    
    def _get_channel_name(self, room_id: UUID) -> str:
        """Get Redis channel name for a chat room."""
        return f"{settings.REDIS_PUBSUB_PREFIX}{str(room_id)}"
    
    async def publish_message(self, room_id: UUID, message: Dict[str, Any]):
        """
        Publish a message to a chat room channel.
        
        Args:
            room_id: Chat room UUID
            message: Message data as dictionary
        """
        if not self._connected:
            await self.connect()
        
        channel = self._get_channel_name(room_id)
        try:
            await self.redis_client.publish(
                channel,
                json.dumps(message, default=str)
            )
            logger.debug(f"Published message to channel {channel}")
        except Exception as e:
            logger.error(f"Failed to publish message to Redis: {e}")
            raise
    
    async def subscribe_to_room(
        self,
        room_id: UUID,
        callback: Callable[[Dict[str, Any]], None]
    ):
        """
        Subscribe to a chat room channel and process messages.
        
        Args:
            room_id: Chat room UUID
            callback: Async function to call with each message
        """
        if not self._connected:
            await self.connect()
        
        channel = self._get_channel_name(room_id)
        self.pubsub = self.redis_client.pubsub()
        
        try:
            await self.pubsub.subscribe(channel)
            logger.info(f"Subscribed to channel {channel}")
            
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
redis_service = RedisService()
