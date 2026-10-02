import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, model_validator


class TagCreate(BaseModel):
    """Validate the name and optional color for a new tag."""

    name: str = Field(..., min_length=1, max_length=50)
    color: str | None = Field(None, max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        """Remove surrounding whitespace before validating the tag name."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("color", mode="before")
    @classmethod
    def strip_color(cls, value: object) -> object:
        """Normalize blank colors to ``None``."""
        if isinstance(value, str):
            return value.strip() or None
        return value


class TagUpdate(BaseModel):
    """Validate fields supplied when updating a tag."""

    name: str | None = Field(None, min_length=1, max_length=50)
    color: str | None = Field(None, max_length=20)

    @field_validator("name", mode="before")
    @classmethod
    def strip_name(cls, value: object) -> object:
        """Remove surrounding whitespace before validating the tag name."""
        return value.strip() if isinstance(value, str) else value

    @field_validator("color", mode="before")
    @classmethod
    def strip_color(cls, value: object) -> object:
        """Normalize blank colors to ``None``."""
        if isinstance(value, str):
            return value.strip() or None
        return value

    @model_validator(mode="after")
    def validate_patch(self):
        """Require an update field and reject a null tag name."""
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided")
        if "name" in self.model_fields_set and self.name is None:
            raise ValueError("name cannot be null")
        return self


class TagResponse(BaseModel):
    """Return a tag with its ownership and timestamp fields."""

    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    color: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TagListResponse(BaseModel):
    """Return the authenticated user's tags."""

    items: list[TagResponse]
