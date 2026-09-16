import asyncio
import os
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from app.api.deps import get_redis
from app.core.security import create_access_token
from app.db.base import Base
from app.db.session import get_db
from app.models import Tag, TodoTag  # noqa: F401 — THÊM: đăng ký bảng tags cho SQLite test DB
from app.main import app

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
test_session_maker = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class MockRedisClient:
    """THÊM: in-memory Redis — hỗ trợ test cache invalidation (delete_by_prefix)."""

    def __init__(self) -> None:
        self._store: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self._store.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._store[key] = value

    async def delete(self, key: str) -> None:
        self._store.pop(key, None)

    async def delete_by_prefix(self, prefix: str) -> None:
        for key in [k for k in self._store if k.startswith(prefix)]:
            del self._store[key]

    async def exists(self, key: str) -> bool:
        return key in self._store

    def clear(self) -> None:
        self._store.clear()


mock_redis = MockRedisClient()


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_db():
    mock_redis.clear()
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
def redis_store() -> MockRedisClient:
    return mock_redis


async def register_and_get_token(
    client: AsyncClient, email: str, password: str = "password123"
) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.fixture
def auth_headers() -> dict:
    token = create_access_token(data={"sub": "00000000-0000-0000-0000-000000000001"})
    return {"Authorization": f"Bearer {token}"}
