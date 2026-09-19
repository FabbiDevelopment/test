import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.tag import TagResponse


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoBulkStatusUpdate(BaseModel):
    """
    Schema nhận payload yêu cầu cập nhật trạng thái hoàn thành cho nhiều Todo cùng lúc.
    - todo_ids: danh sách các UUID công việc cần cập nhật.
    - completed: trạng thái hoàn thành mới (true/false).
    """
    todo_ids: list[uuid.UUID] = Field(..., min_length=1, description="Danh sách ID công việc")
    completed: bool = Field(..., description="Trạng thái hoàn thành mới")


class TodoResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    completed: bool
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_email: str | None = None
    tags: list[TagResponse] = []  # Danh sách các Tag đính kèm với công việc này

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    items: list[TodoResponse]
    total: int
    page: int
    size: int
