import redis.asyncio as aioredis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self._redis = None

    async def initialize(self):
        try:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        except Exception:
            self._redis = None

    async def close(self):
        if self._redis:
            try:
                await self._redis.close()
            except Exception:
                pass

    @property
    def client(self):
        return self._redis

    async def get(self, key: str) -> str | None:
        if not self._redis:
            return None
        try:
            return await self._redis.get(key)
        except Exception:
            return None

    async def set(self, key: str, value: str, ex: int | None = None):
        if not self._redis:
            return None
        try:
            await self._redis.set(key, value, ex=ex)
        except Exception:
            pass

    async def delete(self, key: str):
        if not self._redis:
            return None
        try:
            await self._redis.delete(key)
        except Exception:
            pass

    async def exists(self, key: str) -> bool:
        if not self._redis:
            return False
        try:
            return await self._redis.exists(key)
        except Exception:
            return False


redis_client = RedisClient()
