from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TagBase(BaseModel):
    name: str = Field(..., max_length=50)
    color: str | None = Field(None, max_length=20)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=20)


class TagResponse(TagBase):
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
