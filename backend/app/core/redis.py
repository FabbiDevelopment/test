import fnmatch
import redis.asyncio as aioredis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self._redis = None
        self._in_memory: dict[str, str] = {}

    async def initialize(self):
        try:
            client = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
            # Test connection with a short timeout
            await client.ping()
            self._redis = client
            print("Connected to Redis successfully.")
        except Exception:
            self._redis = None
            print("Redis server not reachable on localhost. Using in-memory fallback cache.")

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
        if self._redis:
            try:
                return await self._redis.get(key)
            except Exception:
                pass
        return self._in_memory.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        if self._redis:
            try:
                await self._redis.set(key, value, ex=ex)
                return
            except Exception:
                pass
        self._in_memory[key] = value

    async def delete(self, key: str):
        if self._redis:
            try:
                await self._redis.delete(key)
                return
            except Exception:
                pass
        self._in_memory.pop(key, None)

    async def delete_pattern(self, pattern: str):
        if self._redis:
            try:
                async for key in self._redis.scan_iter(match=pattern):
                    await self._redis.delete(key)
                return
            except Exception:
                pass
        # In-memory pattern matching
        keys_to_delete = [k for k in self._in_memory if fnmatch.fnmatch(k, pattern)]
        for k in keys_to_delete:
            self._in_memory.pop(k, None)


redis_client = RedisClient()
