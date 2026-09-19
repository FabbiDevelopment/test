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
    get_tag_by_name_lower,
    get_tags_by_user,
    update_tag,
)

router = APIRouter()
async def invalidate_user_todos_cache(redis: RedisClient, user_id: uuid.UUID) -> None:
    
    try:
        if redis.client:
            keys = await redis.client.keys(f"todos:list:{user_id}:*")
            if keys:
                await redis.client.delete(*keys)
    except Exception:
        pass


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    tags = await get_tags_by_user(db, user_id=current_user.id)
    return tags


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):

    existing_tag = await get_tag_by_name_lower(db, user_id=current_user.id, name=tag_data.name)
    if existing_tag:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tag with this name already exists",
        )

    tag = await create_tag(db, tag_data=tag_data, user_id=current_user.id)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_tag_by_id(db, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this tag",
        )

    if tag_data.name and tag_data.name.strip().lower() != tag.name.lower():
        existing_tag = await get_tag_by_name_lower(db, user_id=current_user.id, name=tag_data.name)
        if existing_tag:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tag with this name already exists",
            )

    updated_tag = await update_tag(db, tag=tag, tag_data=tag_data)
    await invalidate_user_todos_cache(redis, current_user.id)
    return updated_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_tag_by_id(db, tag_id=tag_id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this tag",
        )

    await delete_tag(db, tag=tag)
    await invalidate_user_todos_cache(redis, current_user.id)
    return None
