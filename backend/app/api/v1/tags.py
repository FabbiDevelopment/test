import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate

router = APIRouter()


async def _invalidate_todos(redis: RedisClient, user_id: uuid.UUID) -> None:
    await redis.delete_pattern(f"todos:{user_id}:*")


async def _owned_tag(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag:
    tag = await db.scalar(select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id))
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


async def _ensure_unique_name(
    db: AsyncSession, user_id: uuid.UUID, name: str, exclude_id: uuid.UUID | None = None
) -> None:
    query = select(Tag.id).where(
        Tag.user_id == user_id, func.lower(Tag.name) == name.lower()
    )
    if exclude_id:
        query = query.where(Tag.id != exclude_id)
    if await db.scalar(query):
        raise HTTPException(status_code=409, detail="Tag name already exists")


@router.get("", response_model=list[TagResponse])
async def list_tags(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Tag).where(Tag.user_id == current_user.id).order_by(func.lower(Tag.name))
    )
    return list(result.scalars().all())


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    tag_data: TagCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_unique_name(db, current_user.id, tag_data.name)
    tag = Tag(user_id=current_user.id, **tag_data.model_dump())
    db.add(tag)
    try:
        await db.flush()
        await db.refresh(tag)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tag name already exists") from exc
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(
    tag_id: uuid.UUID,
    tag_data: TagUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await _owned_tag(db, tag_id, current_user.id)
    values = tag_data.model_dump(exclude_unset=True)
    if "name" in values:
        if values["name"] is None:
            raise HTTPException(status_code=422, detail="Tag name cannot be null")
        await _ensure_unique_name(db, current_user.id, values["name"], tag.id)
    for key, value in values.items():
        setattr(tag, key, value)
    try:
        await db.flush()
        await db.refresh(tag)
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(status_code=409, detail="Tag name already exists") from exc
    await _invalidate_todos(redis, current_user.id)
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(
    tag_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    tag = await _owned_tag(db, tag_id, current_user.id)
    await db.delete(tag)
    await db.flush()
    await _invalidate_todos(redis, current_user.id)
