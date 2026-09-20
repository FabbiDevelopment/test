import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, get_redis
from app.core.redis import RedisClient
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
async def list_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all tags belonging to the current user."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.name.asc())
    )
    tags = result.scalars().all()
    return tags


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_in: TagCreate,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Create a new tag for the current user."""
    # Check case-insensitive uniqueness per user
    existing_result = await db.execute(
        select(Tag).where(
            Tag.user_id == current_user.id,
            func.lower(Tag.name) == tag_in.name.strip().lower(),
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A tag with this name already exists",
        )

    tag = Tag(
        user_id=current_user.id,
        name=tag_in.name.strip(),
        color=tag_in.color or "#3b82f6",
    )
    db.add(tag)
    await db.commit()
    await db.refresh(tag)

    # Invalidate todos cache for current user
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_in: TagUpdate,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Update a tag's name or color."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tag",
        )

    if tag_in.name is not None and tag_in.name.strip().lower() != tag.name.lower():
        existing_result = await db.execute(
            select(Tag).where(
                Tag.user_id == current_user.id,
                Tag.id != tag_id,
                func.lower(Tag.name) == tag_in.name.strip().lower(),
            )
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A tag with this name already exists",
            )
        tag.name = tag_in.name.strip()

    if tag_in.color is not None:
        tag.color = tag_in.color

    await db.commit()
    await db.refresh(tag)

    # Invalidate cache
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")

    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a tag and detach it from all todos."""
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    tag = result.scalar_one_or_none()

    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )
    if tag.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this tag",
        )

    await db.delete(tag)
    await db.commit()

    # Invalidate cache
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
