"""Security tests for authentication and JWT tokens."""

from datetime import timedelta
import uuid
import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_expired_token_rejected(client: AsyncClient):
    """Test that an expired JWT access token is rejected with 401."""
    # Register user to have a valid user in DB
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired@example.com", "password": "password123"},
    )
    assert reg_response.status_code == 201

    # Get user id from /api/v1/auth/me using initial valid token
    valid_token = reg_response.json()["access_token"]
    me_resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    user_id = me_resp.json()["id"]

    # Create an expired token (expired 10 seconds ago)
    expired_token = create_access_token(
        data={"sub": str(user_id)},
        expires_delta=timedelta(seconds=-10),
    )

    # Attempt to access protected endpoint with expired token
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_tampered_token_rejected(client: AsyncClient):
    """Test that a tampered JWT token (modified signature/payload) is rejected with 401."""
    # Register user
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "tamper@example.com", "password": "password123"},
    )
    valid_token = reg_response.json()["access_token"]

    # Tamper with the token by modifying the last characters of signature
    tampered_token = valid_token[:-4] + "xxxx" if not valid_token.endswith("xxxx") else valid_token[:-4] + "yyyy"

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
    assert "Invalid authentication token" in response.json()["detail"]


@pytest.mark.asyncio
async def test_refresh_token_rejected_as_access(client: AsyncClient):
    """Test that a refresh token cannot be used to authenticate access-protected endpoints."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refreshtoken@example.com", "password": "password123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    # Use refresh token to access /auth/me
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401
    assert "Invalid token type" in response.json()["detail"]


@pytest.mark.asyncio
async def test_nonexistent_user_token_rejected(client: AsyncClient):
    """Test that a validly signed token with a non-existent user UUID is rejected."""
    random_user_id = str(uuid.uuid4())
    token = create_access_token(data={"sub": random_user_id})

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401
    assert "User not found" in response.json()["detail"]
