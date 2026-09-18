import uuid

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


class DuplicateTagNameError(Exception):
    """Raised when a user already has a tag with this name (case-insensitive)."""


async def get_tags(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc())
    )
    return list(result.scalars().all())


async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag | None:
    """Fetch a tag, scoped to its owner (same IDOR-safe pattern as todos)."""
    result = await db.execute(
        select(Tag).where(Tag.id == tag_id, Tag.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def get_tags_by_ids(
    db: AsyncSession, tag_ids: list[uuid.UUID], user_id: uuid.UUID
) -> list[Tag]:
    """Fetch multiple tags at once, scoped to their owner."""
    if not tag_ids:
        return []
    result = await db.execute(
        select(Tag).where(Tag.id.in_(tag_ids), Tag.user_id == user_id)
    )
    return list(result.scalars().all())


async def _name_taken(
    db: AsyncSession, user_id: uuid.UUID, name: str, exclude_tag_id: uuid.UUID | None = None
) -> bool:
    query = select(func.count()).select_from(Tag).where(
        Tag.user_id == user_id, func.lower(Tag.name) == name.lower()
    )
    if exclude_tag_id is not None:
        query = query.where(Tag.id != exclude_tag_id)
    result = await db.execute(query)
    return result.scalar_one() > 0


async def create_tag(db: AsyncSession, tag_data: TagCreate, user_id: uuid.UUID) -> Tag:
    if await _name_taken(db, user_id, tag_data.name):
        raise DuplicateTagNameError(tag_data.name)

    tag = Tag(user_id=user_id, name=tag_data.name, color=tag_data.color)
    db.add(tag)
    try:
        await db.flush()
    except IntegrityError:
        # Race condition: two requests created the same name concurrently.
        # The DB-level unique index (uq_tags_user_id_lower_name) is the
        # real guard; convert the low-level error into our domain error.
        await db.rollback()
        raise DuplicateTagNameError(tag_data.name)
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, tag_data: TagUpdate) -> Tag:
    update_fields = tag_data.model_dump(exclude_unset=True)

    if "name" in update_fields and update_fields["name"] is not None:
        if await _name_taken(db, tag.user_id, update_fields["name"], exclude_tag_id=tag.id):
            raise DuplicateTagNameError(update_fields["name"])
        tag.name = update_fields["name"]

    if "color" in update_fields:
        tag.color = update_fields["color"]

    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise DuplicateTagNameError(update_fields.get("name", tag.name))
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    # ON DELETE CASCADE on todo_tags.tag_id cleans up every attachment.
    await db.delete(tag)
    await db.flush()
