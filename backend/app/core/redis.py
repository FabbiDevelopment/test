import redis.asyncio as aioredis

from app.core.config import settings


class RedisClient:
    def __init__(self):
        self._redis = None

    async def initialize(self):
        self._redis = aioredis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )

    async def close(self):
        if self._redis:
            await self._redis.close()

    @property
    def client(self):
        return self._redis

    async def get(self, key: str) -> str | None:
        return await self._redis.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        await self._redis.set(key, value, ex=ex)

    async def delete(self, key: str):
        await self._redis.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern using SCAN + DEL.

        Bug #5 fix: used to invalidate user-scoped cache keys after
        todo create/update/delete mutations.
        Example: delete_pattern("todos:list:{user_id}:*")
        """
        deleted = 0
        async for key in self._redis.scan_iter(match=pattern):
            await self._redis.delete(key)
            deleted += 1
        return deleted

    async def set_blacklist(self, jti: str, ttl_seconds: int) -> None:
        """Blacklist a JWT jti for the remainder of its lifetime.

        Bug #8 fix: stores jti in Redis so that logged-out tokens cannot
        be reused even before they naturally expire.
        """
        await self._redis.set(f"token:blacklist:{jti}", "1", ex=ttl_seconds)

    async def is_blacklisted(self, jti: str) -> bool:
        """Check whether a JWT jti has been blacklisted (i.e. logged out).

        Bug #8 fix: called in get_current_user dependency to reject
        tokens whose owners have already logged out.
        """
        return bool(await self._redis.exists(f"token:blacklist:{jti}"))


redis_client = RedisClient()
