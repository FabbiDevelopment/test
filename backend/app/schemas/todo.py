import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.schemas.tag import TagResponse


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TodoResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    completed: bool
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_email: str | None = None
    tags: list[TagResponse] = Field(default_factory=list)

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    items: list[TodoResponse]
    total: int
    page: int
    size: int


class TodoTagAttach(BaseModel):
    tag_id: uuid.UUID


class TodoBulkStatusUpdate(BaseModel):
    todo_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=100)
    completed: bool

    @field_validator("todo_ids")
    @classmethod
    def require_unique_ids(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("todo_ids must not contain duplicates")
        return value


class TodoBulkStatusResponse(BaseModel):
    updated_count: int
    completed: bool
