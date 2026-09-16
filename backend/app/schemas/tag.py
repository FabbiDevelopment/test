import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class TagCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    color: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Tag name cannot be blank")
        return normalized


class TagUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    color: str | None = Field(default=None, max_length=20)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Tag name cannot be blank")
        return normalized

    @model_validator(mode="after")
    def require_at_least_one_field(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        return self


class TagResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
