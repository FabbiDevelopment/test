import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str | None = Field(default="#6366f1", max_length=20)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, max_length=20)


class TagResponse(TagBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    items: list[TagResponse]
    total: int


class AttachTagRequest(BaseModel):
    tag_id: uuid.UUID


class BulkStatusUpdateRequest(BaseModel):
    todo_ids: list[uuid.UUID] = Field(..., min_length=1)
    completed: bool


class BulkStatusUpdateResponse(BaseModel):
    updated_count: int
