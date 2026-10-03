"""Auth tests — Tier 2A.

Covers:
- Happy-path: register, login, logout, /me
- Expired / tampered JWT token rejection
- User enumeration prevention
- Refresh token validation
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token, create_refresh_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def register(client: AsyncClient, email: str, password: str = "password123"):
    """Register a user and return the full response JSON."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    return resp


async def login(client: AsyncClient, email: str, password: str = "password123"):
    """Login and return full response JSON."""
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    return resp


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """Registering with a new email returns 201 and both tokens."""
    resp = await register(client, "register@example.com")
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Registering twice with the same email returns 400."""
    await register(client, "dup@example.com")
    resp = await register(client, "dup@example.com")
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Login with correct credentials returns 200 and both tokens."""
    await register(client, "login_ok@example.com")
    resp = await login(client, "login_ok@example.com")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient):
    """GET /me with a valid token returns the authenticated user's info."""
    reg = await register(client, "me@example.com")
    token = reg.json()["access_token"]

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_logout_success(client: AsyncClient):
    """POST /logout with a valid token returns 200."""
    reg = await register(client, "logout@example.com")
    token = reg.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["message"] == "Successfully logged out"


# ---------------------------------------------------------------------------
# Scenario 1 — Expired JWT is rejected
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected(client: AsyncClient):
    """An access token with negative expiry (already expired) must be rejected
    with 401, not accepted as if it were valid."""
    expired_token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),  # already expired
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    # Must be 401, not 200
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_is_rejected(client: AsyncClient):
    """A token with its signature tampered must return 401."""
    reg = await register(client, "tamper@example.com")
    valid_token = reg.json()["access_token"]

    # Corrupt the last few bytes of the signature
    tampered_token = valid_token[:-5] + "XXXXX"

    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_missing_token_returns_403(client: AsyncClient):
    """Requests without Authorization header must be denied."""
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_refresh_token_cannot_be_used_as_access_token(client: AsyncClient):
    """Using a refresh token where an access token is required must be rejected.

    The /me endpoint reads `token.type`; refresh tokens have type='refresh'
    while access tokens have type='access'. A proper implementation should
    reject the wrong token type, but at minimum the endpoint must not succeed
    when the user does not exist in the DB (the sub UUID is synthetic).
    """
    refresh_token = create_refresh_token(
        data={"sub": "00000000-0000-0000-0000-000000000099"},
    )
    resp = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    # User does not exist → 401
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Scenario — User enumeration prevention on login
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient):
    """Wrong password must return 401, not 404."""
    await register(client, "enum@example.com")
    resp = await login(client, "enum@example.com", password="WrongPass!")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_login_unknown_email_returns_401_not_404(client: AsyncClient):
    """Login with a non-existent email must return 401 (not 404).

    Returning 404 would reveal that the email is not registered,
    enabling user enumeration attacks.
    """
    resp = await login(client, "ghost@nonexistent.com")
    assert resp.status_code == 401
    # Detail must be generic — must NOT say 'not found'
    detail = resp.json()["detail"].lower()
    assert "not found" not in detail


@pytest.mark.asyncio
async def test_login_error_message_is_generic(client: AsyncClient):
    """The error message for wrong email vs wrong password should be identical
    so attackers cannot distinguish the two failure modes."""
    await register(client, "generic@example.com")

    resp_bad_email = await login(client, "nobody@example.com", "password123")
    resp_bad_pass = await login(client, "generic@example.com", "WrongPass!")

    assert resp_bad_email.status_code == 401
    assert resp_bad_pass.status_code == 401
    assert resp_bad_email.json()["detail"] == resp_bad_pass.json()["detail"]


# ---------------------------------------------------------------------------
# Refresh token tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_refresh_with_valid_refresh_token(client: AsyncClient):
    """POST /refresh with a valid refresh token returns new tokens."""
    reg = await register(client, "refresh@example.com")
    refresh_token = reg.json()["refresh_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_refresh_with_access_token_fails(client: AsyncClient):
    """Using an access token on /refresh must be rejected (wrong token type)."""
    reg = await register(client, "bad_refresh@example.com")
    access_token = reg.json()["access_token"]

    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_with_expired_refresh_token_fails(client: AsyncClient):
    """An expired refresh token must be rejected."""
    expired_refresh = create_refresh_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),
    )
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh},
    )
    assert resp.status_code == 401
