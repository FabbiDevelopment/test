import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.core.redis import RedisClient
from app.models.user import User
from app.schemas.tag import TagCreate, TagListResponse, TagResponse, TagUpdate
from app.services.tag_service import (
    create_tag,
    delete_tag,
    get_tag_by_id_and_user,
    get_tags,
    update_tag,
)

router = APIRouter()

CACHE_TTL_TAGS = 300  # 5 minutes for tag listing


async def delete_user_tags_cache(redis: RedisClient, user_id: uuid.UUID):
    """Invalidate cached tags list for a specific user."""
    if redis.client:
        await redis.client.delete(f"tags:user:{user_id}")


async def delete_user_todos_cache(redis: RedisClient, user_id: uuid.UUID):
    """Invalidate all cached todo lists for a specific user."""
    if redis.client:
        keys = await redis.client.keys(f"todos:user:{user_id}:*")
        if keys:
            await redis.client.delete(*keys)


@router.get("", response_model=TagListResponse)
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """List all tags owned by the authenticated user with Redis caching."""
    cache_key = f"tags:user:{current_user.id}"
    cached = await redis.get(cache_key)
    if cached:
        cached_data = json.loads(cached)
        return TagListResponse(**cached_data)

    tags = await get_tags(db, current_user.id)
    response = TagListResponse(items=[TagResponse.model_validate(t) for t in tags])
    await redis.set(cache_key, response.model_dump_json(), ex=CACHE_TTL_TAGS)
    return response


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a new tag with case-insensitive uniqueness check."""
    tag = await create_tag(db, tag_data, current_user.id)
    await delete_user_tags_cache(redis, current_user.id)
    return TagResponse.model_validate(tag)


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update tag name or color."""
    tag = await get_tag_by_id_and_user(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    updated = await update_tag(db, tag, tag_data.model_dump(exclude_unset=True))
    await delete_user_tags_cache(redis, current_user.id)
    await delete_user_todos_cache(redis, current_user.id)
    return TagResponse.model_validate(updated)


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a tag and cascade remove associations from todos."""
    tag = await get_tag_by_id_and_user(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await delete_tag(db, tag)
    await delete_user_tags_cache(redis, current_user.id)
    await delete_user_todos_cache(redis, current_user.id)

