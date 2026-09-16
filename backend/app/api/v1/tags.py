import uuid

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.cache_service import invalidate_todo_cache
from app.services.tag_service import (
    create_tag,
    get_tag_by_id,
    get_tag_by_name,
    list_tags,
)

router = APIRouter()


@router.get("", response_model=list[TagResponse])
async def get_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await list_tags(db, current_user.id)


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if await get_tag_by_name(db, tag_data.name, current_user.id):
        raise HTTPException(status_code=409, detail="Tag name already exists")

    try:
        return await create_tag(db, tag_data, current_user.id)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Tag name already exists",
        ) from exc


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_existing_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag_data.name is not None:
        duplicate = await get_tag_by_name(db, tag_data.name, current_user.id)
        if duplicate is not None and duplicate.id != tag.id:
            raise HTTPException(status_code=409, detail="Tag name already exists")

    for field, value in tag_data.model_dump(exclude_unset=True).items():
        setattr(tag, field, value)

    try:
        await db.flush()
        await db.refresh(tag)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Tag name already exists",
        ) from exc

    await invalidate_todo_cache(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")

    await db.delete(tag)
    await db.flush()
    await invalidate_todo_cache(redis, current_user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
