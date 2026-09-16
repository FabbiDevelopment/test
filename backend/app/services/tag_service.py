import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate


async def list_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(func.lower(Tag.name), Tag.id)
    )
    return list(result.scalars().all())


async def get_tag_by_id(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_tag_by_name(
    db: AsyncSession, name: str, user_id: uuid.UUID
) -> Tag | None:
    result = await db.execute(
        select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == name.lower(),
        )
    )
    return result.scalar_one_or_none()


async def create_tag(db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID) -> Tag:
    tag = Tag(user_id=user_id, **tag_data.model_dump())
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag
