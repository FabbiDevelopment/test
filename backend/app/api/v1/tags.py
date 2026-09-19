import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
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
    get_tags,
    update_tag,
)
from app.services.todo_cache_service import commit_todo_mutation

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List only the authenticated user's Tags."""
    return await get_tags(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Create a Tag owned by the authenticated user."""
    try:
        tag = await create_tag(db, tag_data, current_user.id)
    except IntegrityError:
        await db.rollback()
        raise _duplicate_name_error() from None
    await commit_todo_mutation(db, redis, current_user.id)
    return tag


@router.get("/{tag_id}", response_model=TagResponse)
async def get_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get one of the authenticated user's Tags without exposing other users' Tags."""
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise _tag_not_found()
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Partially update only the authenticated user's Tag."""
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise _tag_not_found()
    try:
        updated_tag = await update_tag(db, tag, tag_data.model_dump(exclude_unset=True))
    except IntegrityError:
        await db.rollback()
        raise _duplicate_name_error() from None
    await commit_todo_mutation(db, redis, current_user.id)
    return updated_tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Delete only the authenticated user's Tag and its Todo mappings."""
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise _tag_not_found()
    await delete_tag(db, tag)
    await commit_todo_mutation(db, redis, current_user.id)
    return None


def _tag_not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")


def _duplicate_name_error() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail="A tag with this name already exists",
    )
