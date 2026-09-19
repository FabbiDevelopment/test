import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_access_token, get_current_user, get_redis
from app.core.redis import RedisClient
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    create_refresh_token,
    token_remaining_seconds,
    verify_password,
    verify_token,
)
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.auth_service import create_user, get_user_by_email, get_user_by_id

router = APIRouter()


async def issue_token_pair(
    redis: RedisClient,
    user_id: uuid.UUID,
    session_id: str | None = None,
) -> TokenResponse:
    """Issue an access/refresh pair and persist its one-time refresh session."""
    session_id = session_id or str(uuid.uuid4())
    token_data = {"sub": str(user_id), "sid": session_id}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    refresh_payload = verify_token(refresh_token)
    if refresh_payload is None:
        raise RuntimeError("Generated refresh token could not be verified")

    await redis.create_refresh_session(
        session_id=session_id,
        token_id=refresh_payload["jti"],
        user_id=str(user_id),
        ttl_seconds=token_remaining_seconds(refresh_payload),
    )
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post(
    "/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Register a new user."""
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    try:
        user = await create_user(db, user_data)
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    return await issue_token_pair(redis, user.id)


@router.post("/login", response_model=TokenResponse)
async def login(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Authenticate user and return tokens."""
    user = await get_user_by_email(db, user_data.email)
    password_hash = user.hashed_password if user else DUMMY_PASSWORD_HASH
    if not user or not verify_password(user_data.password, password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return await issue_token_pair(redis, user.id)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis),
):
    """Refresh access token using refresh token."""
    payload = verify_token(request.refresh_token)

    if (
        payload is None
        or payload.get("type") != "refresh"
        or not isinstance(payload.get("jti"), str)
        or not isinstance(payload.get("sid"), str)
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user_id = payload.get("sub")
    try:
        user_uuid = uuid.UUID(user_id)
        uuid.UUID(payload["sid"])
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    if await get_user_by_id(db, user_uuid) is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    token_data = {"sub": str(user_uuid), "sid": payload["sid"]}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)
    new_refresh_payload = verify_token(refresh_token)
    if new_refresh_payload is None:
        raise RuntimeError("Generated refresh token could not be verified")

    rotated = await redis.rotate_refresh_session(
        session_id=payload["sid"],
        old_token_id=payload["jti"],
        new_token_id=new_refresh_payload["jti"],
        user_id=str(user_uuid),
        ttl_seconds=token_remaining_seconds(new_refresh_payload),
    )
    if not rotated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/logout")
async def logout(
    payload: dict = Depends(get_current_access_token),
    redis: RedisClient = Depends(get_redis),
):
    """Revoke the current access/refresh session."""
    await redis.revoke_session(
        session_id=payload["sid"],
        access_token_ttl_seconds=token_remaining_seconds(payload),
    )
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user information."""
    return current_user
