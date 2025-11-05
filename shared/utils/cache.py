"""
Caching utilities using Redis.
"""

import orjson
from typing import Optional, Any
from redis.asyncio import Redis
from shared.config.settings import settings


class CacheManager:
    """Redis-based cache manager."""

    def __init__(self) -> None:
        self.redis: Optional[Redis] = None
        self.ttl = settings.cache_ttl_seconds

    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = await Redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=False
        )

    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.redis:
            return None

        value = await self.redis.get(key)
        if value:
            return orjson.loads(value)
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """
        Set value in cache.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds (defaults to settings.cache_ttl_seconds)

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        serialized = orjson.dumps(value)
        await self.redis.setex(key, ttl or self.ttl, serialized)
        return True

    async def delete(self, key: str) -> bool:
        """
        Delete value from cache.

        Args:
            key: Cache key

        Returns:
            True if successful
        """
        if not self.redis:
            return False

        await self.redis.delete(key)
        return True
