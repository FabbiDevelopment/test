import uuid
from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.core.config import settings
from app.models.tag import Tag
from app.models.todo import Todo
from app.schemas.todo import TodoCreate, TodoListParams


def normalize_date_filter(
    value: date | datetime, end_of_day: bool = False
) -> datetime:
    """Convert date-only app-local boundaries to UTC for timestamp comparisons."""
    if isinstance(value, datetime):
        normalized_value = value
        if normalized_value.tzinfo is None:
            normalized_value = normalized_value.replace(tzinfo=timezone.utc)
    else:
        app_timezone = timezone(timedelta(hours=settings.APP_UTC_OFFSET_HOURS))
        normalized_value = datetime.combine(value, time.min, tzinfo=app_timezone)

    if end_of_day:
        normalized_value = normalized_value.replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
    return normalized_value.astimezone(timezone.utc)


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
    return todo


def build_todo_filters(user_id: uuid.UUID, params: TodoListParams):
    """Build owner-scoped todo filters, including an optional tag filter."""
    filters = [Todo.user_id == user_id]

    if params.status == "completed":
        filters.append(Todo.completed.is_(True))
    elif params.status == "active":
        filters.append(Todo.completed.is_(False))

    if params.tag_id is not None:
        filters.append(
            Todo.tags.any((Tag.id == params.tag_id) & (Tag.user_id == user_id))
        )

    if params.normalized_keyword:
        filters.append(
            or_(
                Todo.title.icontains(params.normalized_keyword, autoescape=True),
                Todo.description.icontains(params.normalized_keyword, autoescape=True),
            )
        )

    if params.date_from is not None:
        filters.append(Todo.created_at >= normalize_date_filter(params.date_from))
    if params.date_to is not None:
        filters.append(
            Todo.created_at
            <= normalize_date_filter(params.date_to, end_of_day=True)
        )

    return filters


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    params: TodoListParams,
) -> tuple[list[Todo], int]:
    """Get a filtered, paginated todo list scoped to one owner."""
    filters = build_todo_filters(user_id, params)
    query = (
        select(Todo)
        .options(selectinload(Todo.tags), joinedload(Todo.user))
        .where(*filters)
        .order_by(Todo.created_at.desc(), Todo.id.desc())
        .offset((params.page - 1) * params.effective_page_size)
        .limit(params.effective_page_size)
    )
    result = await db.execute(query)
    todos = list(result.scalars().all())

    count_query = select(func.count(Todo.id)).where(*filters)
    total = await db.scalar(count_query)
    return todos, total or 0


async def get_todo_by_id(
    db: AsyncSession, todo_id: uuid.UUID, user_id: uuid.UUID
) -> Todo | None:
    """Get a todo with its tags only when it belongs to the requesting user."""
    result = await db.execute(
        select(Todo)
        .options(
            selectinload(Todo.tags), 
            joinedload(Todo.user)
        )
        .where(Todo.id == todo_id, Todo.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    for key, value in update_data.items():
        if key in {"title", "completed"} and value is None:
            continue
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
    return todo


async def bulk_update_todo_status(
    db: AsyncSession,
    user_id: uuid.UUID,
    todo_ids: list[uuid.UUID],
    completed: bool,
) -> int | None:
    """Update the completed status of multiple todos owned by the user."""
    result = await db.execute(
        select(Todo.id).where(Todo.user_id == user_id, Todo.id.in_(todo_ids))
    )
    owned_ids = set(result.scalars().all())
    if owned_ids != set(todo_ids):
        return None

    await db.execute(
        update(Todo)
        .where(Todo.user_id == user_id, Todo.id.in_(todo_ids))
        .values(completed=completed, updated_at=func.now())
    )
    return len(owned_ids)


def attach_tag(todo: Todo, tag: Tag) -> bool:
    """Attach a tag to a todo unless the relationship already exists."""
    if any(existing.id == tag.id for existing in todo.tags):
        return False
    todo.tags.append(tag)
    return True


def detach_tag(todo: Todo, tag: Tag) -> bool:
    """Remove a tag from a todo and report whether it was attached."""
    if not any(existing.id == tag.id for existing in todo.tags):
        return False
    todo.tags.remove(tag)
    return True


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    await db.delete(todo)
    await db.flush()
