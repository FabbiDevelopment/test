import uuid
from datetime import datetime

from pydantic import BaseModel, Field


HEX_COLOR_REGEX = r"^#(?:[0-9a-fA-F]{3}){1,2}$"


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: str | None = Field(None, pattern=HEX_COLOR_REGEX)


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, pattern=HEX_COLOR_REGEX)


class TagResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str | None = None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagSimpleResponse(BaseModel):
    id: uuid.UUID
    name: str
    color: str | None = None

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    items: list[TagResponse]

