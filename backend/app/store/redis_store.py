import logging

from upstash_redis.asyncio import Redis

from app.store.memory_store import MemoryStore

logger = logging.getLogger(__name__)


class RedisStore:
    def __init__(self, redis: Redis):
        self._redis = redis

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, px: int | None = None, nx: bool = False) -> bool:
        return bool(await self._redis.set(key, value, px=px, nx=nx or None))

    async def delete(self, key: str) -> None:
        await self._redis.delete(key)

    async def incr(self, key: str, expire_seconds: int) -> int:
        count = await self._redis.incr(key)
        if count == 1:
            await self._redis.expire(key, expire_seconds)
        return count


class FallbackStore:
    """
    Uses Redis, and falls back to process memory for cache reads and writes when it fails.
    Counters are not covered: if Redis is down, incr raises so the budget fails closed.
    """

    def __init__(self, primary: RedisStore, fallback: MemoryStore):
        self._primary = primary
        self._fallback = fallback

    async def get(self, key: str) -> str | None:
        try:
            return await self._primary.get(key)
        except Exception:
            logger.exception("redis get failed, using memory fallback")
            return await self._fallback.get(key)

    async def set(self, key: str, value: str, px: int | None = None, nx: bool = False) -> bool:
        try:
            return await self._primary.set(key, value, px=px, nx=nx)
        except Exception:
            logger.exception("redis set failed, using memory fallback")
            return await self._fallback.set(key, value, px=px, nx=nx)

    async def delete(self, key: str) -> None:
        try:
            await self._primary.delete(key)
        except Exception:
            logger.exception("redis delete failed, using memory fallback")
            await self._fallback.delete(key)

    async def incr(self, key: str, expire_seconds: int) -> int:
        return await self._primary.incr(key, expire_seconds)
