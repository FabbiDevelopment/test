"""Auth tests."""

from datetime import timedelta

import pytest
from httpx import AsyncClient

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
async def test_register_duplicate_email(client: AsyncClient):
    """Test duplicate email registration is rejected."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


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
    """Test expired access tokens cannot authenticate protected endpoints."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired@example.com", "password": "password123"},
    )
    user_response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {reg_response.json()['access_token']}",
        },
    )
    user_id = user_response.json()["id"]
    expired_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_cannot_authenticate_protected_route(client: AsyncClient):
    """Test refresh tokens are rejected by access-token protected endpoints."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-as-access@example.com", "password": "password123"},
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {reg_response.json()['refresh_token']}"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_access_token_cannot_refresh_tokens(client: AsyncClient):
    """Test access tokens are rejected by the refresh endpoint."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "access-as-refresh@example.com", "password": "password123"},
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": reg_response.json()["access_token"]},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_is_rotated_and_old_token_revoked(client: AsyncClient):
    """Test refresh token reuse is rejected after a successful rotation."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "rotate@example.com", "password": "password123"},
    )
    old_refresh_token = reg_response.json()["refresh_token"]

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_response.status_code == 200

    reuse_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert reuse_response.status_code == 401

    new_refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_response.json()["refresh_token"]},
    )
    assert new_refresh_response.status_code == 200


@pytest.mark.asyncio
async def test_logout_revokes_current_access_token(client: AsyncClient):
    """Test logging out blacklists the access token used for logout."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "revoke-access@example.com", "password": "password123"},
    )
    access_token = reg_response.json()["access_token"]

    logout_response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert logout_response.status_code == 200

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_current_access_and_refresh_tokens(client: AsyncClient):
    """Test logout blacklists both submitted access and refresh tokens."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "revoke-both@example.com", "password": "password123"},
    )
    tokens = reg_response.json()

    logout_response = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert logout_response.status_code == 200

    access_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert access_response.status_code == 401

    refresh_response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )
    assert refresh_response.status_code == 401


@pytest.mark.asyncio
async def test_expired_refresh_token_is_rejected(client: AsyncClient):
    """Test expired refresh tokens cannot issue new tokens."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired-refresh@example.com", "password": "password123"},
    )
    user_response = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {reg_response.json()['access_token']}",
        },
    )
    expired_refresh_token = create_refresh_token(
        data={"sub": user_response.json()["id"]},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh_token},
    )

    assert response.status_code == 401
