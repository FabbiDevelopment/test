import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.api.v1.todos import _invalidate_list_cache
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.tag_service import (
    DuplicateTagNameError,
    create_tag,
    delete_tag,
    get_tag_by_id,
    get_tags,
    update_tag,
)

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all tags of the authenticated user."""
    return await get_tags(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new tag. Tag names are unique per user, case-insensitively."""
    try:
        return await create_tag(db, tag_data, current_user.id)
    except DuplicateTagNameError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a tag named '{tag_data.name}'",
        )


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Rename/update a tag. Scoped to the current user to prevent IDOR."""
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    try:
        updated_tag = await update_tag(db, tag, tag_data)
    except DuplicateTagNameError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have a tag named '{tag_data.name}'",
        )

    # Renaming/recoloring a tag changes what any cached todo list (which
    # embeds each todo's tags) would render, so invalidate it.
    await _invalidate_list_cache(redis, current_user.id)

    return updated_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete a tag and its todo-tag relations. Scoped to the current user."""
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tag not found",
        )

    await delete_tag(db, tag)
    await _invalidate_list_cache(redis, current_user.id)

    return None
