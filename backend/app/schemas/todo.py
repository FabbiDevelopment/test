import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.tag import TagResponse

TodoStatus = Literal["active", "completed", "all"]


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


class TodoListParams(BaseModel):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=10_000)
    # Keep `size` for existing clients that still use the old parameter.
    size: int | None = Field(None, ge=1, le=10_000)
    status: TodoStatus | None = None
    tag_id: uuid.UUID | None = None
    keyword: str | None = Field(None, max_length=200)
    date_from: date | None = None
    date_to: date | None = None

    @model_validator(mode="after")
    def validate_date_range(self):
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        return self

    @property
    def effective_page_size(self) -> int:
        return self.size or self.page_size

    @property
    def normalized_keyword(self) -> str | None:
        keyword = self.keyword.strip() if self.keyword else ""
        return keyword or None


class BulkTodoStatusUpdate(BaseModel):
    todo_ids: list[uuid.UUID] = Field(..., min_length=1, max_length=500)
    completed: bool

    @model_validator(mode="after")
    def reject_duplicate_ids(self):
        if len(set(self.todo_ids)) != len(self.todo_ids):
            raise ValueError("todo_ids must not contain duplicates")
        return self


class TodoTagCreate(BaseModel):
    """Validate the tag ID used to attach a tag to a todo."""

    tag_id: uuid.UUID
