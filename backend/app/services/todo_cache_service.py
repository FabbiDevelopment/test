import logging
import uuid

from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.redis import RedisClient

logger = logging.getLogger(__name__)


def todo_cache_version_key(user_id: uuid.UUID) -> str:
    return f"todos:list:{user_id}:version"


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.incr(todo_cache_version_key(user_id))


async def commit_todo_mutation(
    db: AsyncSession,
    redis: RedisClient,
    user_id: uuid.UUID,
) -> None:
    """Commit a Todo-affecting mutation before best-effort cache invalidation."""
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    try:
        await invalidate_todo_cache(redis, user_id)
    except RedisError:
        logger.warning(
            "todo_cache_invalidation_failed",
            extra={"user_id": str(user_id)},
            exc_info=True,
        )
