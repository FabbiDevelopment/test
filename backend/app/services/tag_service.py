import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.tag import TagCreate, TagUpdate


async def get_tags_by_user(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
    )
    return list(result.scalars().all())


async def get_tag_by_id(db: AsyncSession, tag_id: uuid.UUID) -> Tag | None:
    result = await db.execute(select(Tag).where(Tag.id == tag_id))
    return result.scalar_one_or_none()


async def get_tag_by_name_insensitive(
    db: AsyncSession, user_id: uuid.UUID, name: str
) -> Tag | None:
    # THÊM: case-insensitive duplicate check — "Work" và "work" coi là trùng
    result = await db.execute(
        select(Tag).where(
            Tag.user_id == user_id,
            func.lower(Tag.name) == name.lower(),
        )
    )
    return result.scalar_one_or_none()


async def create_tag(db: AsyncSession, user_id: uuid.UUID, data: TagCreate) -> Tag:
    tag = Tag(user_id=user_id, name=data.name.strip(), color=data.color)
    db.add(tag)
    await db.flush()
    await db.refresh(tag)
    return tag


async def update_tag(db: AsyncSession, tag: Tag, data: TagUpdate) -> Tag:
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        if key == "name" and value is not None:
            setattr(tag, key, value.strip())
        else:
            setattr(tag, key, value)
    await db.flush()
    await db.refresh(tag)
    return tag


async def delete_tag(db: AsyncSession, tag: Tag) -> None:
    await db.delete(tag)
    await db.flush()


async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    existing = await db.execute(
        select(TodoTag).where(TodoTag.todo_id == todo.id, TodoTag.tag_id == tag.id)
    )
    if existing.scalar_one_or_none() is None:
        db.add(TodoTag(todo_id=todo.id, tag_id=tag.id))
        await db.flush()


async def detach_tag_from_todo(
    db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID
) -> None:
    result = await db.execute(
        select(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    )
    link = result.scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.flush()


async def get_tags_for_todo(db: AsyncSession, todo_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag)
        .join(TodoTag, TodoTag.tag_id == Tag.id)
        .where(TodoTag.todo_id == todo_id)
    )
    return list(result.scalars().all())
