import os
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Set the test database before importing app modules because app.db.session creates
# its engine at import time. These imports are intentionally delayed (E402).
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["JWT_SECRET"] = "test-only-jwt-secret"

from app.api.deps import get_redis  # noqa: E402
from app.core.security import create_access_token  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def override_get_redis():
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.incr = AsyncMock(return_value=1)
    mock_redis.create_refresh_session = AsyncMock()
    mock_redis.rotate_refresh_session = AsyncMock(return_value=True)
    mock_redis.revoke_session = AsyncMock()
    mock_redis.is_session_revoked = AsyncMock(return_value=False)
    return mock_redis


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_redis] = override_get_redis


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with test_session_maker() as session:
        yield session


@pytest.fixture
def shared_redis():
    """Provide one in-memory Redis mock shared by all requests in a test."""
    cache: dict[str, str] = {}
    refresh_sessions: dict[str, tuple[str, str]] = {}
    session_refresh_tokens: dict[str, str] = {}
    revoked_sessions: set[str] = set()
    mock_redis = MagicMock()

    async def get(key: str) -> str | None:
        return cache.get(key)

    async def set_value(key: str, value: str, ex: int | None = None) -> None:
        cache[key] = value

    async def delete(*keys: str) -> int:
        deleted = 0
        for key in keys:
            if key in cache:
                deleted += 1
                del cache[key]
        return deleted

    async def incr(key: str) -> int:
        value = int(cache.get(key, "0")) + 1
        cache[key] = str(value)
        return value

    async def create_refresh_session(
        session_id: str,
        token_id: str,
        user_id: str,
        ttl_seconds: int,
    ) -> None:
        refresh_sessions[token_id] = (session_id, user_id)
        session_refresh_tokens[session_id] = token_id

    async def rotate_refresh_session(
        session_id: str,
        old_token_id: str,
        new_token_id: str,
        user_id: str,
        ttl_seconds: int,
    ) -> bool:
        if session_id in revoked_sessions or refresh_sessions.get(old_token_id) != (
            session_id,
            user_id,
        ):
            return False
        del refresh_sessions[old_token_id]
        refresh_sessions[new_token_id] = (session_id, user_id)
        session_refresh_tokens[session_id] = new_token_id
        return True

    async def revoke_session(
        session_id: str,
        access_token_ttl_seconds: int,
    ) -> None:
        revoked_sessions.add(session_id)
        token_id = session_refresh_tokens.pop(session_id, None)
        if token_id:
            refresh_sessions.pop(token_id, None)

    async def is_session_revoked(session_id: str) -> bool:
        return session_id in revoked_sessions

    mock_redis.get = AsyncMock(side_effect=get)
    mock_redis.set = AsyncMock(side_effect=set_value)
    mock_redis.delete = AsyncMock(side_effect=delete)
    mock_redis.incr = AsyncMock(side_effect=incr)
    mock_redis.create_refresh_session = AsyncMock(side_effect=create_refresh_session)
    mock_redis.rotate_refresh_session = AsyncMock(side_effect=rotate_refresh_session)
    mock_redis.revoke_session = AsyncMock(side_effect=revoke_session)
    mock_redis.is_session_revoked = AsyncMock(side_effect=is_session_revoked)

    previous_override = app.dependency_overrides.get(get_redis)
    app.dependency_overrides[get_redis] = lambda: mock_redis
    yield mock_redis

    if previous_override is None:
        app.dependency_overrides.pop(get_redis, None)
    else:
        app.dependency_overrides[get_redis] = previous_override


@pytest.fixture
def auth_headers() -> dict:
    """Create auth headers with a valid token for testing."""
    token = create_access_token(
        data={
            "sub": "00000000-0000-0000-0000-000000000001",
            "sid": "00000000-0000-0000-0000-000000000002",
        }
    )
    return {"Authorization": f"Bearer {token}"}
