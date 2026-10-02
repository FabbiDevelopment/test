import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagListResponse, TagResponse, TagUpdate
from app.services.tag_service import (
    create_user_tag,
    get_user_tag,
    list_user_tags,
    update_user_tag,
)

router = APIRouter()


async def invalidate_user_todos(redis: RedisClient, user_id: uuid.UUID) -> None:
    """Clear the user's cached todo lists after tag changes."""
    await redis.delete_pattern(f"todos:{user_id}:list:*")


@router.get("", response_model=TagListResponse)
async def get_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List tags owned by the authenticated user."""
    return TagListResponse(items=await list_user_tags(db, current_user.id))


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a tag for the authenticated user."""
    try:
        tag = await create_user_tag(db, current_user.id, tag_data.name, tag_data.color)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        ) from exc

    await invalidate_user_todos(redis, current_user.id)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update one of the authenticated user's tags."""
    tag = await get_user_tag(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_data = tag_data.model_dump(exclude_unset=True)

    try:
        tag = await update_user_tag(db, tag, update_data)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A tag with this name already exists",
        ) from exc

    await invalidate_user_todos(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete one of the authenticated user's tags."""
    tag = await get_user_tag(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.commit()
    await invalidate_user_todos(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
