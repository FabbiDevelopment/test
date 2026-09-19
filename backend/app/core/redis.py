import redis.asyncio as aioredis

from app.core.config import settings

CREATE_REFRESH_SESSION_SCRIPT = """
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[3])
redis.call('SET', KEYS[2], ARGV[2], 'EX', ARGV[3])
redis.call('SET', KEYS[3], ARGV[1] .. ':' .. ARGV[2], 'EX', ARGV[3])
return 1
"""

ROTATE_REFRESH_SESSION_SCRIPT = """
if redis.call('GET', KEYS[1]) ~= ARGV[1] then return 0 end
if redis.call('GET', KEYS[2]) ~= ARGV[1] .. ':' .. ARGV[2] then return 0 end
redis.call('DEL', KEYS[2])
redis.call('SET', KEYS[3], ARGV[1] .. ':' .. ARGV[3], 'EX', ARGV[4])
redis.call('SET', KEYS[1], ARGV[1], 'EX', ARGV[4])
redis.call('SET', KEYS[4], ARGV[3], 'EX', ARGV[4])
return 1
"""

REVOKE_SESSION_SCRIPT = """
local refresh_jti = redis.call('GET', KEYS[2])
if refresh_jti then redis.call('DEL', ARGV[1] .. refresh_jti) end
redis.call('DEL', KEYS[1], KEYS[2])
redis.call('SET', KEYS[3], '1', 'EX', ARGV[2])
return 1
"""


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

    async def incr(self, key: str) -> int:
        return await self._redis.incr(key)

    async def exists(self, key: str) -> bool:
        return await self._redis.exists(key)

    @staticmethod
    def _session_key(session_id: str) -> str:
        return f"auth:session:{session_id}"

    @staticmethod
    def _session_refresh_key(session_id: str) -> str:
        return f"auth:session:{session_id}:refresh"

    @staticmethod
    def _refresh_key(token_id: str) -> str:
        return f"auth:refresh:{token_id}"

    @staticmethod
    def _revoked_session_key(session_id: str) -> str:
        return f"auth:session:{session_id}:revoked"

    async def create_refresh_session(
        self,
        session_id: str,
        token_id: str,
        user_id: str,
        ttl_seconds: int,
    ) -> None:
        await self._redis.eval(
            CREATE_REFRESH_SESSION_SCRIPT,
            3,
            self._session_key(session_id),
            self._session_refresh_key(session_id),
            self._refresh_key(token_id),
            user_id,
            token_id,
            ttl_seconds,
        )

    async def rotate_refresh_session(
        self,
        session_id: str,
        old_token_id: str,
        new_token_id: str,
        user_id: str,
        ttl_seconds: int,
    ) -> bool:
        result = await self._redis.eval(
            ROTATE_REFRESH_SESSION_SCRIPT,
            4,
            self._session_key(session_id),
            self._refresh_key(old_token_id),
            self._refresh_key(new_token_id),
            self._session_refresh_key(session_id),
            user_id,
            old_token_id,
            new_token_id,
            ttl_seconds,
        )
        return bool(result)

    async def revoke_session(
        self,
        session_id: str,
        access_token_ttl_seconds: int,
    ) -> None:
        await self._redis.eval(
            REVOKE_SESSION_SCRIPT,
            3,
            self._session_key(session_id),
            self._session_refresh_key(session_id),
            self._revoked_session_key(session_id),
            "auth:refresh:",
            access_token_ttl_seconds,
        )

    async def is_session_revoked(self, session_id: str) -> bool:
        return bool(await self._redis.exists(self._revoked_session_key(session_id)))


redis_client = RedisClient()
