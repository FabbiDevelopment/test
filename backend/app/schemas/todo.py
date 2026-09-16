import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = None


class TodoUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    completed: bool | None = None


class TagBrief(BaseModel):
    # THÊM: tag summary trong todo response — Level 4
    id: uuid.UUID
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}


class TodoResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    completed: bool
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    user_email: str | None = None
    tags: list[TagBrief] = []  # THÊM: tags đính kèm todo

    model_config = {"from_attributes": True}


class TodoListResponse(BaseModel):
    items: list[TodoResponse]
    total: int
    page: int
    size: int
