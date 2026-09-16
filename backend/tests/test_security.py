"""Security tests: JWT expiration and forged token rejection."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings
from tests.conftest import register_and_get_token


@pytest.mark.asyncio
async def test_expired_access_token_rejected(client: AsyncClient):
    """Expired JWT access tokens must be rejected with 401."""
    token = await register_and_get_token(client, "expired@example.com")

    # Verify valid token works first
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_response.status_code == 200

    expired_payload = {
        "sub": me_response.json()["id"],
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "type": "access",
    }
    expired_token = jwt.encode(
        expired_payload,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_forged_access_token_rejected(client: AsyncClient):
    """Tokens signed with wrong secret must be rejected with 401."""
    await register_and_get_token(client, "forged@example.com")

    forged_payload = {
        "sub": "00000000-0000-0000-0000-000000000099",
        "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        "type": "access",
    }
    forged_token = jwt.encode(
        forged_payload,
        "wrong-secret-key",
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_protected_routes(client: AsyncClient):
    """Refresh tokens must not be accepted on protected endpoints."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-as-access@example.com", "password": "password123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401
    assert "token type" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_missing_token_rejected(client: AsyncClient):
    """Requests without Bearer token must be rejected."""
    response = await client.get("/api/v1/todos")
    assert response.status_code == 403
