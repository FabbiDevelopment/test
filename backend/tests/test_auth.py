"""Auth tests."""

import pytest
from httpx import AsyncClient


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
async def test_expired_token_rejected(client: AsyncClient):
    """Test that an expired JWT token is rejected with 401."""
    from datetime import timedelta
    from app.core.security import create_access_token

    expired_token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-60),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


@pytest.mark.asyncio
async def test_tampered_token_rejected(client: AsyncClient):
    """Test that a tampered JWT token is rejected with 401."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "tamper@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]
    tampered_token = token[:-5] + "XXXXX"

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"


@pytest.mark.asyncio
async def test_refresh_token_cannot_access_protected_endpoint(client: AsyncClient):
    """Test that a refresh token cannot be used to authenticate access-protected endpoints."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refreshtest@example.com", "password": "password123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_user_enumeration_prevention(client: AsyncClient):
    """Test that login returns identical 401 error for both missing user and wrong password."""
    # Register valid user
    await client.post(
        "/api/v1/auth/register",
        json={"email": "enum_test@example.com", "password": "correct_password"},
    )

    # 1. Non-existent user
    resp_nonexistent = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "password123"},
    )
    assert resp_nonexistent.status_code == 401
    assert resp_nonexistent.json()["detail"] == "Incorrect email or password"

    # 2. Existing user with wrong password
    resp_wrong_pw = await client.post(
        "/api/v1/auth/login",
        json={"email": "enum_test@example.com", "password": "wrong_password"},
    )
    assert resp_wrong_pw.status_code == 401
    assert resp_wrong_pw.json()["detail"] == "Incorrect email or password"
