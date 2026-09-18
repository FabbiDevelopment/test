import os
import time
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# The application's default engine is never used by these tests.
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:////tmp/assessment-unused-test-engine.db"
os.environ["DB_ECHO"] = "false"

from app.api.deps import get_redis  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402


class MemoryRedis:
    """Stateful cache fake: shared across requests, including real expiry semantics."""

    def __init__(self):
        self.data = {}
        self.expiry = {}
        self.deleted = []
        self.hits = 0

    async def get(self, key):
        if self.expiry.get(key, float("inf")) <= time.monotonic():
            self.data.pop(key, None)
        value = self.data.get(key)
        self.hits += value is not None
        return value

    async def set(self, key, value, ex=None):
        self.data[key] = value
        if ex is not None:
            self.expiry[key] = time.monotonic() + ex

    async def keys(self, pattern):
        prefix = pattern.removesuffix("*")
        return [key for key in self.data if key.startswith(prefix)]

    async def delete(self, key):
        self.deleted.append(key)
        self.data.pop(key, None)


@pytest.fixture
async def db_factory(tmp_path):
    engine = create_async_engine(f"sqlite+aiosqlite:///{tmp_path}/test.db")

    @event.listens_for(engine.sync_engine, "connect")
    def foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    yield factory
    await engine.dispose()


@pytest.fixture
async def db_session(db_factory):
    async with db_factory() as session:
        yield session


@pytest.fixture
def redis_cache():
    return MemoryRedis()


@pytest.fixture
async def client(db_factory, redis_cache) -> AsyncGenerator[AsyncClient, None]:
    async def override_db():
        async with db_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_redis] = lambda: redis_cache
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
