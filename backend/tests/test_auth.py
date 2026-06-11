"""Auth tests."""

import pytest
from datetime import timedelta
from httpx import AsyncClient
from app.core.security import create_access_token


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


# ── NEW SECURITY TESTS ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_expired_token_is_rejected(client: AsyncClient):
    """Expired tokens must be rejected with 401 (validates verify_exp fix)."""
    # Create a token that expired 1 second in the past
    expired_token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401, (
        f"Expected 401 for expired token, got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_login_wrong_email_returns_401_not_404(client: AsyncClient):
    """Login with non-existent email must return 401, not 404 (no user enumeration)."""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypassword"},
    )
    assert response.status_code == 401, (
        f"Expected 401 to prevent user enumeration, got {response.status_code}"
    )


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    """Login with wrong password must return 401."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "wrongpw@example.com", "password": "correct_password"},
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpw@example.com", "password": "wrong_password"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email_rejected(client: AsyncClient):
    """Registering with an already-used email must be rejected."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "password123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup@example.com", "password": "different_password"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_refresh_deleted_user_returns_401(client: AsyncClient):
    """Refresh token for a user that no longer exists must return 401.

    We create a refresh token whose 'sub' (user UUID) was never inserted into
    the test database, simulating a deleted user.
    """
    from datetime import timedelta
    from app.core.security import create_refresh_token

    # Fabricate a refresh token for a non-existent user UUID
    ghost_refresh = create_refresh_token(
        data={"sub": "aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"},
        expires_delta=timedelta(days=7),
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": ghost_refresh},
    )
    assert response.status_code == 401, (
        f"Expected 401 for deleted user refresh, got {response.status_code}: {response.text}"
    )
