"""Auth tests — including security scenarios."""

from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, verify_token


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
    """Test that registering with an already-used email returns 400."""
    payload = {"email": "dup@example.com", "password": "password123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


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
async def test_login_wrong_password_returns_401_not_404(client: AsyncClient):
    """Bug fix test: login should return 401 with a uniform message to prevent
    username enumeration (old code returned 404 for missing user vs 401 for wrong pass).
    """
    await client.post(
        "/api/v1/auth/register",
        json={"email": "enum@example.com", "password": "correct_pass"},
    )
    # Wrong password on existing account
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "enum@example.com", "password": "wrong_pass"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

    # Non-existent email — must return same status + message
    response2 = await client.post(
        "/api/v1/auth/login",
        json={"email": "no_such_user@example.com", "password": "any_pass"},
    )
    assert response2.status_code == 401
    assert response2.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_expired_token_is_rejected(client: AsyncClient):
    """Security test: a token with a past expiry must be rejected (verify_exp=True fix)."""
    registered = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired@example.com", "password": "password123"},
    )
    token = registered.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert (await client.get("/api/v1/auth/me", headers=headers)).status_code == 200
    claims = verify_token(token)
    expired_token = create_access_token(
        data={"sub": claims["sub"]},
        expires_delta=timedelta(hours=-1),
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_is_rejected(client: AsyncClient):
    """Security test: a token with an invalid signature must be rejected."""
    tampered_token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJoYWNrZXIifQ.INVALIDSIG"
    )
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401


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
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "logout@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    response = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Successfully logged out"
