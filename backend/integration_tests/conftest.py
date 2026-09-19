"""Fixtures for tests that exercise the Compose PostgreSQL and Redis services.

Run these separately from ``tests/`` because the fast suite intentionally
replaces both services with SQLite and mocks.
"""

import uuid
from collections.abc import AsyncGenerator
from dataclasses import dataclass, field

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from app.core.redis import redis_client
from app.core.security import verify_token
from app.db.session import async_session_maker
from app.main import app
from app.models.todo import Todo
from app.models.user import User


@dataclass
class IntegrationContext:
    client: AsyncClient
    user_ids: set[uuid.UUID] = field(default_factory=set)
    session_ids: set[str] = field(default_factory=set)

    async def register_user(self) -> tuple[dict[str, str], dict[str, str]]:
        email = f"integration-{uuid.uuid4().hex}@example.com"
        response = await self.client.post(
            "/api/v1/auth/register",
            json={"email": email, "password": "Integration@123"},
        )
        assert response.status_code == 201, response.text

        tokens = response.json()
        access_payload = verify_token(tokens["access_token"])
        assert access_payload is not None
        self.user_ids.add(uuid.UUID(access_payload["sub"]))
        self.session_ids.add(access_payload["sid"])
        return tokens, {"Authorization": f"Bearer {tokens['access_token']}"}

    def track_token_pair(self, tokens: dict[str, str]) -> None:
        access_payload = verify_token(tokens["access_token"])
        assert access_payload is not None
        self.session_ids.add(access_payload["sid"])

    async def cleanup(self) -> None:
        for session_id in self.session_ids:
            refresh_key = f"auth:session:{session_id}:refresh"
            refresh_jti = await redis_client.get(refresh_key)
            keys = [
                f"auth:session:{session_id}",
                refresh_key,
                f"auth:session:{session_id}:revoked",
            ]
            if refresh_jti:
                keys.append(f"auth:refresh:{refresh_jti}")
            await redis_client.client.delete(*keys)

        for user_id in self.user_ids:
            cache_keys = [
                key
                async for key in redis_client.client.scan_iter(
                    match=f"todos:list:{user_id}:*"
                )
            ]
            if cache_keys:
                await redis_client.client.delete(*cache_keys)

        if self.user_ids:
            async with async_session_maker() as session:
                await session.execute(
                    delete(Todo).where(Todo.user_id.in_(self.user_ids))
                )
                await session.execute(delete(User).where(User.id.in_(self.user_ids)))
                await session.commit()


@pytest_asyncio.fixture(loop_scope="function")
async def integration_context() -> AsyncGenerator[IntegrationContext, None]:
    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://integration-test",
        ) as client:
            context = IntegrationContext(client=client)
            try:
                yield context
            finally:
                await context.cleanup()
