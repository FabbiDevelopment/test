import uuid

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.tag import TagCreate, TagUpdate
from app.services.todo_service import TAG_LOAD


async def get_tags_for_user(db: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    return list(
        (
            await db.scalars(
                select(Tag).where(Tag.user_id == user_id).order_by(Tag.name)
            )
        ).all()
    )


async def get_tags_for_todo(db: AsyncSession, todo_id: uuid.UUID) -> list[Tag]:
    result = await db.execute(
        select(Tag)
        .join(TodoTag, TodoTag.tag_id == Tag.id)
        .where(TodoTag.todo_id == todo_id)
        .order_by(Tag.name)
    )
    return list(result.scalars().all())


async def owned_tag(db: AsyncSession, tag_id: uuid.UUID, user_id: uuid.UUID) -> Tag:
    tag = await db.get(Tag, tag_id)
    if tag is None:
        raise HTTPException(status_code=404, detail="Tag not found")
    if tag.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized to access this tag")
    return tag


async def save_tag(db: AsyncSession, tag: Tag) -> Tag:
    try:
        await db.flush()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=409, detail="Tag name already exists (case-insensitive)"
        )
    return tag


async def create_tag(db: AsyncSession, data: TagCreate, user_id: uuid.UUID) -> Tag:
    tag = Tag(**data.model_dump(), user_id=user_id)
    db.add(tag)
    return await save_tag(db, tag)


async def update_tag(db: AsyncSession, tag: Tag, data: TagUpdate) -> Tag:
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(tag, key, value)
    return await save_tag(db, tag)


async def delete_tag(db: AsyncSession, tag: Tag):
    await db.delete(tag)
    await db.flush()


async def attach_tag_to_todo(db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID):
    # ON CONFLICT makes concurrent identical attachments idempotent at DB level.
    if db.bind.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    await db.execute(
        insert(TodoTag).values(todo_id=todo_id, tag_id=tag_id).on_conflict_do_nothing()
    )


async def detach_tag_from_todo(db: AsyncSession, todo_id: uuid.UUID, tag_id: uuid.UUID):
    from sqlalchemy import delete

    await db.execute(
        delete(TodoTag).where(TodoTag.todo_id == todo_id, TodoTag.tag_id == tag_id)
    )


async def bulk_update_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    completed: bool,
    user_id: uuid.UUID,
) -> list[Todo]:
    # Lock in a stable order; reject a mixed-owner batch BEFORE changing any row.
    owned_ids = list(
        (
            await db.scalars(
                select(Todo.id)
                .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
                .order_by(Todo.id)
                .with_for_update()
            )
        ).all()
    )
    if len(owned_ids) != len(todo_ids):
        raise HTTPException(
            status_code=403, detail="All todos must exist and belong to you"
        )
    await db.execute(
        update(Todo).where(Todo.id.in_(owned_ids)).values(completed=completed)
    )
    return list(
        (
            await db.scalars(
                select(Todo)
                .where(Todo.id.in_(owned_ids))
                .options(TAG_LOAD)
                .order_by(Todo.created_at.desc(), Todo.id.desc())
                .execution_options(populate_existing=True)
            )
        ).all()
    )
