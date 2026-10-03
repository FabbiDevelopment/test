import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.tag import Tag, TodoTag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


# ── helpers ───────────────────────────────────────────────────────────────────

def _todo_query_with_tags():
    """Base select that eagerly loads the tags relationship."""
    return select(Todo).options(selectinload(Todo.tags))


# ── CRUD ──────────────────────────────────────────────────────────────────────

async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=user_id,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo, attribute_names=["tags"])
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,          # "active" | "completed"
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[list[Todo], int]:
    """Filtered, paginated todo list ordered by created_at DESC, id DESC."""
    base = _todo_query_with_tags().where(Todo.user_id == user_id)

    if status == "completed":
        base = base.where(Todo.completed.is_(True))
    elif status == "active":
        base = base.where(Todo.completed.is_(False))

    if keyword:
        pattern = f"%{keyword}%"
        base = base.where(Todo.title.ilike(pattern))

    if date_from:
        base = base.where(Todo.created_at >= date_from)
    if date_to:
        base = base.where(Todo.created_at <= date_to)

    if tag_id:
        base = base.where(
            Todo.id.in_(
                select(TodoTag.todo_id).where(TodoTag.tag_id == tag_id)
            )
        )

    # Count before pagination
    count_q = select(func.count()).select_from(base.subquery())
    total = (await db.execute(count_q)).scalar_one()

    query = base.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)
    todos = list((await db.execute(query)).scalars().all())

    return todos, total


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    result = await db.execute(
        _todo_query_with_tags().where(Todo.id == todo_id)
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo, attribute_names=["tags"])
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


# ── Tag attachment ────────────────────────────────────────────────────────────

async def attach_tag_to_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> Todo:
    """Attach tag to todo (idempotent — ignores if already attached)."""
    existing = await db.execute(
        select(TodoTag).where(
            TodoTag.todo_id == todo.id, TodoTag.tag_id == tag.id
        )
    )
    if not existing.scalar_one_or_none():
        db.add(TodoTag(todo_id=todo.id, tag_id=tag.id))
        await db.flush()
    await db.refresh(todo, attribute_names=["tags"])
    return todo


async def detach_tag_from_todo(
    db: AsyncSession, todo: Todo, tag: Tag
) -> None:
    """Detach tag from todo. Raises ValueError if mapping does not exist."""
    result = await db.execute(
        select(TodoTag).where(
            TodoTag.todo_id == todo.id, TodoTag.tag_id == tag.id
        )
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise ValueError("Tag is not attached to this todo.")
    await db.delete(mapping)
    await db.flush()


# ── Bulk update ───────────────────────────────────────────────────────────────

async def bulk_update_status(
    db: AsyncSession,
    todo_ids: list[uuid.UUID],
    user_id: uuid.UUID,
    completed: bool,
) -> int:
    """
    Update completed status for all given todo_ids that belong to user_id.
    Runs in a single UPDATE statement inside the active transaction.
    Returns the number of rows affected.
    """
    result = await db.execute(
        update(Todo)
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
        .values(completed=completed)
        .execution_options(synchronize_session="fetch")
    )
    return result.rowcount
