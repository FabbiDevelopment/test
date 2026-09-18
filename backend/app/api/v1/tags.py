import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_redis
from app.core.redis import RedisClient
from app.db.session import get_db
from app.models.tag import Tag
from app.models.user import User
from app.schemas.tag import TagCreate, TagResponse, TagUpdate
from app.services.todo_service import get_tag_by_id

router = APIRouter()


def normalized(name: str) -> str:
    return name.strip().casefold()


@router.get("", response_model=list[TagResponse])
async def list_tags(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Tag).where(Tag.user_id == current_user.id).order_by(Tag.name))
    return list(result.scalars().all())


@router.post("", response_model=TagResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: TagCreate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = Tag(user_id=current_user.id, name=payload.name.strip(), normalized_name=normalized(payload.name), color=payload.color)
    db.add(tag)
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A tag with this name already exists")
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return tag


@router.patch("/{tag_id}", response_model=TagResponse)
async def update_tag(tag_id: uuid.UUID, payload: TagUpdate, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    tag.name, tag.normalized_name, tag.color = payload.name.strip(), normalized(payload.name), payload.color
    try:
        await db.flush()
    except IntegrityError:
        raise HTTPException(status_code=409, detail="A tag with this name already exists")
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return tag


@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tag(tag_id: uuid.UUID, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db), redis: RedisClient = Depends(get_redis)):
    tag = await get_tag_by_id(db, tag_id, current_user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    await db.delete(tag)
    await db.flush()
    await redis.delete_pattern(f"todos:list:{current_user.id}:*")
    return None
