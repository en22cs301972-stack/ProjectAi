from redis.asyncio import Redis
from app.config import settings
import json
from typing import Any, Optional

redis_client: Optional[Redis] = None


async def init_redis():
    global redis_client
    redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


async def close_redis():
    global redis_client
    if redis_client:
        await redis_client.close()


async def get_redis() -> Redis:
    return redis_client


async def cache_set(key: str, value: Any, expire: int = 300):
    """Set a value in cache with expiration in seconds."""
    if redis_client:
        await redis_client.setex(key, expire, json.dumps(value))


async def cache_get(key: str) -> Optional[Any]:
    """Get a value from cache."""
    if redis_client:
        data = await redis_client.get(key)
        if data:
            return json.loads(data)
    return None


async def cache_delete(key: str):
    """Delete a key from cache."""
    if redis_client:
        await redis_client.delete(key)


async def cache_delete_pattern(pattern: str):
    """Delete all keys matching a pattern."""
    if redis_client:
        keys = await redis_client.keys(pattern)
        if keys:
            await redis_client.delete(*keys)
