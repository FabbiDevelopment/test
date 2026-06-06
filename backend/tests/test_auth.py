"""Auth tests."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, create_refresh_token


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Test successful user registration."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login after registration."""
    # Register first
    await client.post(
        "/api/v1/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    # Then login
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """Test getting current user info."""
    # Register and get token
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    # Get current user
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_logout(client: AsyncClient):
    """Test logout endpoint."""
    # Register and get token
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    # Logout
    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected(client: AsyncClient):
    """Expired access tokens must not authenticate protected routes."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired-access@example.com", "password": "password123"},
    )
    user_id = reg_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {user_id}"},
    )
    expired_token = create_access_token(
        data={"sub": me_response.json()["id"]},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_protected_routes(client: AsyncClient):
    """Refresh tokens are not accepted as bearer access tokens."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-as-access@example.com", "password": "password123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_expired_refresh_token_is_rejected(client: AsyncClient):
    """Expired refresh tokens must not mint new access tokens."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired-refresh@example.com", "password": "password123"},
    )
    access_token = reg_response.json()["access_token"]
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    expired_refresh = create_refresh_token(
        data={"sub": me_response.json()["id"]},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_handles_duplicate_email_race(client: AsyncClient, monkeypatch):
    """A DB uniqueness race is reported as an email conflict."""
    from app.api.v1 import auth

    monkeypatch.setattr(auth, "get_user_by_email", AsyncMock(return_value=None))
    monkeypatch.setattr(
        auth,
        "create_user",
        AsyncMock(
            side_effect=IntegrityError(
                statement="INSERT INTO users",
                params={"email": "race@example.com"},
                orig=Exception("duplicate key"),
            )
        ),
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "race@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"
