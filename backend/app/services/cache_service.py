import hashlib
import json
import uuid
from datetime import datetime

from app.core.redis import RedisClient


def build_todo_cache_key(
    user_id: uuid.UUID,
    *,
    page: int,
    page_size: int,
    status: str | None,
    tag_id: uuid.UUID | None,
    keyword: str | None,
    date_from: datetime | None,
    date_to: datetime | None,
) -> str:
    parameters = {
        "date_from": date_from.isoformat() if date_from else None,
        "date_to": date_to.isoformat() if date_to else None,
        "keyword": keyword.strip() if keyword else None,
        "page": page,
        "page_size": page_size,
        "status": status,
        "tag_id": str(tag_id) if tag_id else None,
    }
    serialized = json.dumps(parameters, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode()).hexdigest()[:24]
    return f"todos:{user_id}:list:{digest}"


async def invalidate_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(f"todos:{user_id}:list:*")
