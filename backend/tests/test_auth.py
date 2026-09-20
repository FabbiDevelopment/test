"""Auth tests."""

import pytest
from httpx import AsyncClient
from jose import jwt

from tests.conftest import create_expired_token, register_user


# ── Existing tests ────────────────────────────────────────────────────────────

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


# ── New Tier 2 tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_expired_token_is_rejected(client: AsyncClient):
    """Tier 2 — Bug #1 regression: expired JWT must return 401.

    Creates a token with a negative expiry delta so it is immediately expired.
    The server must reject it with 401, not grant access.
    """
    expired_token = create_expired_token("00000000-0000-0000-0000-000000000099")

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401, (
        "Expired token should be rejected with 401. "
        "If this fails, verify_exp may still be disabled."
    )


@pytest.mark.asyncio
async def test_tampered_token_is_rejected(client: AsyncClient):
    """Tier 2 — Tampered JWT (wrong secret) must return 401.

    Signs a token with a different secret key — the server must reject it
    because the signature is invalid.
    """
    fake_token = jwt.encode(
        {"sub": "00000000-0000-0000-0000-000000000099", "type": "access", "jti": "fake-jti"},
        "completely-wrong-secret",
        algorithm="HS256",
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {fake_token}"},
    )

    assert response.status_code == 401, (
        "Token signed with wrong secret should be rejected with 401."
    )


@pytest.mark.asyncio
async def test_login_with_unknown_email_returns_401_not_404(client: AsyncClient):
    """Tier 2 — Bug #6 regression: login with non-existent email must return 401.

    Before the fix, the server returned 404 with 'User not found', leaking
    information about registered emails (user enumeration). Now it must return
    a generic 401 with no information about whether the email exists.
    """
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "anypassword"},
    )

    assert response.status_code == 401, (
        "Unknown email login should return 401, not 404. "
        "404 reveals that the email does not exist (user enumeration)."
    )
    # Generic message should not reveal whether the email was the problem
    assert "not found" not in response.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_400(client: AsyncClient):
    """Tier 2 — Bug #9 regression: registering the same email twice must fail."""
    payload = {"email": "dup@example.com", "password": "password123"}

    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201

    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 400, (
        "Duplicate email registration should be rejected with 400."
    )
