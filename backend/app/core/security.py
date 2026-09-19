import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# Precomputed bcrypt hash for unknown-account login attempts. Verifying it keeps
# the public failure path close to the timing of a real password verification.
DUMMY_PASSWORD_HASH = "$2b$12$PsKgCHXE5O6NEVp6e4wRKO7.hDAuoHpekp1zosL6O6aKcRT1Llsb2"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against an existing bcrypt hash."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )
    except ValueError:
        return False


def get_password_hash(password: str) -> str:
    """Create a bcrypt hash compatible with hashes stored by the old Passlib path."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    to_encode.update({"exp": expire, "type": "refresh", "jti": str(uuid.uuid4())})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            options={
                "verify_exp": True,
                "require_exp": True,
                "require_sub": True,
            },
        )
        if "type" not in payload:
            return None
        return payload
    except JWTError:
        return None


def token_remaining_seconds(payload: dict[str, Any]) -> int:
    """Return the remaining JWT lifetime rounded up to a positive TTL."""
    expires_at = datetime.fromtimestamp(int(payload["exp"]), tz=timezone.utc)
    return max(1, int((expires_at - datetime.now(timezone.utc)).total_seconds()) + 1)
