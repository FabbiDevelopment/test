import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    stmt = select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    stmt = select(Tag).where(Tag.id == tag_id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def get_tag_by_name_lower(
    db: AsyncSession, user_id: uuid.UUID, name: str
) -> Tag | None:
    stmt = select(Tag).where(
        Tag.user_id == user_id,
        func.lower(Tag.name) == name.strip().lower(),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_tag(
    db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID
) -> Tag:
    tag = Tag(
        user_id=user_id,
        name=tag_data.name.strip(),
        color=tag_data.color,
    )
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(
    db: AsyncSession, tag: Tag, tag_data: TagUpdate
) -> Tag:
    update_dict = tag_data.model_dump(exclude_unset=True)
    if "name" in update_dict and update_dict["name"] is not None:
        tag.name = update_dict["name"].strip()
    if "color" in update_dict:
        tag.color = update_dict["color"]

    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.flush()
