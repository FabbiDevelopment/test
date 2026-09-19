import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


def validate_bcrypt_password_length(password: str) -> str:
    """bcrypt accepts at most 72 UTF-8 bytes; reject longer values explicitly."""
    if len(password.encode("utf-8")) > 72:
        raise ValueError("Password must not exceed 72 bytes")
    return password


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

    _validate_password_length = field_validator("password")(
        validate_bcrypt_password_length
    )


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)

    _validate_password_length = field_validator("password")(
        validate_bcrypt_password_length
    )


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str
