import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, verify_password, verify_token
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import RefreshTokenRequest, TokenResponse, UserCreate, UserLogin, UserResponse
from app.services.auth_service import create_user, get_user_by_email, get_user_by_id

router = APIRouter()


def issue_tokens(user: User) -> TokenResponse:
    claims = {"sub": str(user.id)}
    return TokenResponse(access_token=create_access_token(claims), refresh_token=create_refresh_token(claims))


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    if await get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=400, detail="Email already registered")
    try:
        user = await create_user(db, user_data)
        return issue_tokens(user)
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Email already registered")


@router.post("/login", response_model=TokenResponse)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(db, user_data.email)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    return issue_tokens(user)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_token(request.refresh_token, expected_type="refresh")
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = await get_user_by_id(db, uuid.UUID(payload["sub"]))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    return issue_tokens(user)


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """The client discards its tokens; server-side session revocation is out of scope."""
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user
