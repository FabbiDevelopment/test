import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag


async def list_user_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    """List a user's tags in case-insensitive name order."""
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(func.lower(Tag.name), Tag.id)
    )
    return list(result.scalars().all())


async def get_user_tag(
    db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID
) -> Tag | None:
    """Find a tag only when it belongs to the requested user."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def create_user_tag(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str,
    color: str | None,
) -> Tag:
    """Create and flush a tag owned by the requested user."""
    tag = Tag(user_id=user_id, name=name, color=color)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_user_tag(db: AsyncSession, tag: Tag, update_data: dict) -> Tag:
    """Apply the supplied fields to a tag and flush the changes."""
    for field, value in update_data.items():
        setattr(tag, field, value)
    await db.flush()
    return tag
