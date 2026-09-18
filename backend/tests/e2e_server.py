"""Isolated application server used by the Playwright test suite."""

import asyncio

import uvicorn

from app.api.deps import get_redis
from app.db.base import Base
from app.db.session import engine
from app.main import app


class InMemoryRedis:
    def __init__(self) -> None:
        self.values: dict[str, str] = {}

    async def get(self, key: str) -> str | None:
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.values[key] = value

    async def delete_pattern(self, pattern: str) -> None:
        prefix = pattern.removesuffix("*")
        for key in list(self.values):
            if key.startswith(prefix):
                del self.values[key]


async def reset_database() -> None:
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)


if __name__ == "__main__":
    asyncio.run(reset_database())
    redis = InMemoryRedis()
    app.dependency_overrides[get_redis] = lambda: redis
    uvicorn.run(app, host="127.0.0.1", port=8000)
