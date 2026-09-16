import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import (
    create_tag,
    delete_tag,
    get_tag_by_id,
    get_tag_by_name_insensitive,
    get_tags_by_user,
    update_tag,
)

router = APIRouter()


async def _invalidate_user_todo_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_by_prefix(f"todos:list:{user_id}:")


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """GET /tags — List all tags for authenticated user."""
    tags = await get_tags_by_user(db, current_user.id)
    return tags


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """POST /tags — Create a new tag."""
    existing = await get_tag_by_name_insensitive(db, current_user.id, data.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Tag with this name already exists",
        )
    tag = await create_tag(db, current_user.id, data)
    # THÊM: invalidate cache khi tạo tag — tag list thay đổi có thể ảnh hưởng filter UI
    await _invalidate_user_todo_cache(redis, current_user.id)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """PATCH /tags/{tag_id} — Rename/update tag."""
    tag = await get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    if data.name:
        dup = await get_tag_by_name_insensitive(db, current_user.id, data.name)
        if dup and dup.id != tag_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tag with this name already exists",
            )

    updated = await update_tag(db, tag, data)
    await _invalidate_user_todo_cache(redis, current_user.id)
    return updated


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """DELETE /tags/{tag_id} — Delete tag and its todo associations."""
    tag = await get_tag_by_id(db, tag_id)
    if not tag or tag.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")

    await delete_tag(db, tag)
    await _invalidate_user_todo_cache(redis, current_user.id)
    return None
