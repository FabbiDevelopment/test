import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

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


TodoStatus = Literal["active", "completed"]


class TodoTagCreate(BaseModel):
    tag_id: uuid.UUID


class BulkTodoStatusUpdate(BaseModel):
    todo_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)
    completed: bool

    @model_validator(mode="after")
    def todo_ids_must_be_unique(self):
        if len(set(self.todo_ids)) != len(self.todo_ids):
            raise ValueError("todo_ids must be unique")
        return self


class BulkTodoStatusResponse(BaseModel):
    updated_count: int
    items: list[TodoResponse]
