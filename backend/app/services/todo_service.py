from datetime import datetime
import uuid

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tag import Tag
from app.models.todo import Todo
from app.models.todo_tag import TodoTag
from app.schemas.todo import TodoCreate


async def create_todo(
    db: AsyncSession, todo_data: TodoCreate, user_id: uuid.UUID
) -> Todo:
    """
    Tạo một Todo mới cho người dùng.
    """
    todo = Todo(
        title=todo_data.title,
        description=todo_data.description,
        user_id=user_id,
    )
    db.add(todo)
    await db.flush()
    await db.refresh(todo)
    return todo


async def get_todos(
    db: AsyncSession,
    user_id: uuid.UUID,
    status: str | None = None,
    tag_id: uuid.UUID | None = None,
    keyword: str | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Todo], int]:
    """
    Lấy danh sách công việc của User hỗ trợ tìm kiếm, lọc theo nhiều tiêu chí và phân trang.
    Yêu cầu thứ tự sắp xếp: created_at DESC, id DESC.
    """
    
    query = select(Todo).where(Todo.user_id == user_id)

    
    if status == "completed":
        query = query.where(Todo.completed.is_(True))
    elif status == "pending":
        query = query.where(Todo.completed.is_(False))

    
    if tag_id:
        query = query.join(TodoTag, Todo.id == TodoTag.todo_id).where(TodoTag.tag_id == tag_id)

    
    if keyword and keyword.strip():
        kw = f"%{keyword.strip()}%"
        query = query.where(Todo.title.ilike(kw) | Todo.description.ilike(kw))

   
    if date_from:
        query = query.where(Todo.created_at >= date_from)
    if date_to:
        query = query.where(Todo.created_at <= date_to)

   
    count_stmt = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar_one()

    
    query = query.order_by(Todo.created_at.desc(), Todo.id.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    todos = list(result.scalars().unique().all())

    return todos, total


async def get_todo_by_id(db: AsyncSession, todo_id: uuid.UUID) -> Todo | None:
    """
    Lấy thông tin công việc theo ID.
    """
    result = await db.execute(select(Todo).where(Todo.id == todo_id))
    return result.scalar_one_or_none()


async def update_todo(db: AsyncSession, todo: Todo, update_data: dict) -> Todo:
    """
    Cập nhật các trường thông tin của một Todo.
    """
    for key, value in update_data.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
    return todo


async def delete_todo(db: AsyncSession, todo: Todo) -> None:
    """
    Xóa công việc khỏi cơ sở dữ liệu.
    """
    await db.delete(todo)
    await db.flush()


async def attach_tag_to_todo(db: AsyncSession, todo: Todo, tag: Tag) -> Todo:
    """
    Gán một Tag vào Todo.
    """
    if tag not in todo.tags:
        todo.tags.append(tag)
        await db.flush()
        await db.refresh(todo)
    return todo


async def detach_tag_from_todo(db: AsyncSession, todo: Todo, tag: Tag) -> Todo:
    """
    Gỡ một Tag ra khỏi Todo.
    """
    if tag in todo.tags:
        todo.tags.remove(tag)
        await db.flush()
        await db.refresh(todo)
    return todo


async def bulk_update_todo_status(
    db: AsyncSession, user_id: uuid.UUID, todo_ids: list[uuid.UUID], completed: bool
) -> int:
    """
    Cập nhật trạng thái hoàn thành cho nhiều Todo cùng lúc trong Database Transaction.
    Trả về số lượng Todo đã cập nhật thành công.
    """
    stmt = (
        update(Todo)
        .where(Todo.id.in_(todo_ids), Todo.user_id == user_id)
        .values(completed=completed, updated_at=datetime.now())
    )
    result = await db.execute(stmt)
    await db.flush()
    return result.rowcount
