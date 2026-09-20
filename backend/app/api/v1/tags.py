import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tags for current user."""
    query = select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.name.asc())
    result = await db.execute(query)
    tags = list(result.scalars().all())
    return tags


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag with case-insensitive unique name per user."""
    existing_query = select(Tag).where(
        Tag.user_id == current_user.id,
        func.lower(Tag.name) == tag_data.name.lower(),
    )
    existing_result = await db.execute(existing_query)
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tag with this name already exists",
        )

    tag = Tag(
        name=tag_data.name.strip(),
        color=tag_data.color,
        user_id=current_user.id,
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Update a tag's name or color."""
    query = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    if tag_data.name is not None and tag_data.name.lower() != tag.name.lower():
        existing_query = select(Tag).where(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == tag_data.name.lower(),
            Tag.id != tag_id,
        )
        existing_result = await db.execute(existing_query)
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tag with this name already exists",
            )
        tag.name = tag_data.name.strip()

    if tag_data.color is not None:
        tag.color = tag_data.color

    await db.flush()
    await db.refresh(tag)
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a tag and its associations."""
    query = select(Tag).where(Tag.id == tag_id, Tag.user_id == current_user.id)
    result = await db.execute(query)
    tag = result.scalar_one_or_none()
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await db.delete(tag)
    await db.flush()
    await redis.delete_pattern(f"todos:{current_user.id}:list:*")
    return None
