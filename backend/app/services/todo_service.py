import uuid
from datetime import date, timedelta

from sqlalchemy import func, or_, select
from sqlalchemy import update as sa_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.orm.attributes import set_committed_value

from app.models.tag import Tag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate


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
    await db.refresh(todo)
    # A brand new todo has no tags yet. Assigning `todo.tags = []` directly
    # would make SQLAlchemy load the *current* collection first (to diff
    # against), which is a lazy load - and a plain attribute assignment
    # doesn't run inside the greenlet context async SQLAlchemy needs for
    # that, so it would raise MissingGreenlet. set_committed_value marks
    # the collection as already-loaded instead, no DB round-trip.
    set_committed_value(todo, "tags", [])
    return todo


def _todo_filters(
    user_id: uuid.UUID,
    status: str | None,
    keyword: str | None,
    date_from: date | None,
    date_to: date | None,
):
    """Shared WHERE conditions for both the list query and its count query."""
    conditions = [Todo.user_id == user_id]

    if status == "completed":
        conditions.append(Todo.completed.is_(True))
    elif status == "active":
        conditions.append(Todo.completed.is_(False))

    if keyword:
        like_pattern = f"%{keyword}%"
        conditions.append(
            or_(Todo.title.ilike(like_pattern), Todo.description.ilike(like_pattern))
        )

    if date_from:
        conditions.append(Todo.created_at >= date_from)

    if date_to:
        # date_to is inclusive of the whole day.
        conditions.append(Todo.created_at < date_to + timedelta(days=1))

    return conditions


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    skip: int = 0,
    limit: int = 20,
    status: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
) -> tuple[list[Todo], int]:
    """Get todos for a user, with optional filtering and pagination.

    Ordering is created_at DESC, id DESC (per README) so pagination stays
    deterministic even when many rows share an identical created_at
    (e.g. bulk-seeded data, or several todos created within the same
    millisecond).
    """
    conditions = _todo_filters(user_id, status, keyword, date_from, date_to)

    query = select(Todo).where(*conditions).options(selectinload(Todo.tags))
    count_query = select(func.count(func.distinct(Todo.id))).select_from(Todo).where(*conditions)

    if tag_id is not None:
        query = query.join(Todo.tags).where(Tag.id == tag_id)
        count_query = count_query.join(Todo.tags).where(Tag.id == tag_id)

    query = (
        query.order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(query)
    todos = list(result.scalars().unique().all())

    total_result = await db.execute(count_query)
    total = total_result.scalar_one()

    return todos, total


async def get_todo_by_id(
    db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID
) -> Todo | None:
    """Fetch a todo, scoped to its owner so other users' todos are never returned."""
    result = await db.execute(
        select(Todo)
        .where(Todo.id == todo_id, Todo.user_id == user_id)
        .options(selectinload(Todo.tags))
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    # Only refresh scalar columns - refreshing with no attribute_names
    # would expire *every* attribute including the already-loaded `tags`
    # relationship, and a later synchronous access to it would then try
    # to lazy-load outside of a greenlet context and raise MissingGreenlet.
    await db.refresh(todo, attribute_names=["title", "description", "completed", "updated_at"])
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()


async def attach_tag(db: AsyncSession, todo: Todo, tag: Tag) -> Todo:
    """Attach a tag to a todo. Idempotent - attaching twice is a no-op."""
    if tag.id not in {t.id for t in todo.tags}:
        todo.tags.append(tag)
        await db.flush()
    return todo


async def detach_tag(db: AsyncSession, todo: Todo, tag_id: uuid.UUID) -> Todo:
    """Detach a tag from a todo. Idempotent - detaching an absent tag is a no-op."""
    todo.tags = [t for t in todo.tags if t.id != tag_id]
    await db.flush()
    return todo


async def bulk_update_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> tuple[list[uuid.UUID], list[uuid.UUID]]:
    """Bulk-set `completed` on the given todos, restricted to ones the user
    owns. Runs as a single UPDATE statement (one transaction - the request's
    AsyncSession is already transactional; see app/db/session.get_db).

    Returns (updated_ids, skipped_ids). skipped_ids covers both
    nonexistent todo IDs and IDs that belong to a different user - the
    ownership check happens in the WHERE clause itself, not as a
    separate lookup, so there is no window where a caller could probe
    for another user's todo IDs.
    """
    unique_ids = list(dict.fromkeys(todo_ids))  # de-dupe, preserve order

    stmt = (
        sa_update(Todo)
        .where(Todo.id.in_(unique_ids), Todo.user_id == user_id)
        .values(completed=completed)
        .returning(Todo.id)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    updated_ids = list(result.scalars().all())
    await db.flush()

    updated_set = set(updated_ids)
    skipped_ids = [tid for tid in unique_ids if tid not in updated_set]

    return updated_ids, skipped_ids
