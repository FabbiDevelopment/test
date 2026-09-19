"""Auth tests."""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User


@pytest.mark.asyncio(loop_scope="session")
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


@pytest.mark.asyncio(loop_scope="session")
async def test_cors_allows_only_configured_origin(client: AsyncClient):
    """CONFIG-002: credentialed CORS is restricted to the configured frontend."""
    allowed_origin = "http://localhost:3000"
    allowed = await client.options(
        "/health",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    rejected = await client.options(
        "/health",
        headers={
            "Origin": "https://untrusted.example.com",
            "Access-Control-Request-Method": "GET",
        },
    )

    assert allowed.headers["access-control-allow-origin"] == allowed_origin
    assert "PATCH" in allowed.headers["access-control-allow-methods"]
    assert "access-control-allow-origin" not in rejected.headers


def test_bcrypt_password_helpers_verify_existing_and_new_hashes():
    """DEP-002: direct bcrypt avoids Passlib's incompatible version lookup."""
    password = "password123"
    existing_bcrypt_hash = (
        "$2b$12$PsKgCHXE5O6NEVp6e4wRKOE9JjLRFjM1ZebL3EqtMwbp.vQt5NY6u"
    )

    new_hash = get_password_hash(password)

    assert new_hash.startswith("$2b$")
    assert verify_password(password, new_hash)
    assert verify_password(password, existing_bcrypt_hash)
    assert not verify_password("wrong-password", new_hash)


@pytest.mark.asyncio(loop_scope="session")
async def test_register_rejects_passwords_bcrypt_cannot_hash(client: AsyncClient):
    """DEP-002: password length is validated before it reaches bcrypt."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "long-password@example.com", "password": "a" * 73},
    )

    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("endpoint", ["register", "login"])
@pytest.mark.parametrize("password", ["", "short"])
async def test_auth_rejects_passwords_shorter_than_six_characters(
    client: AsyncClient,
    endpoint: str,
    password: str,
):
    """AUTH-006: registration and login share the minimum password contract."""
    response = await client.post(
        f"/api/v1/auth/{endpoint}",
        json={
            "email": f"short-{endpoint}-{len(password)}@example.com",
            "password": password,
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_user_email_is_unique_in_database(db_session):
    """DB-001: the database, not only the API pre-check, rejects duplicates."""
    db_session.add(
        User(email="database-unique@example.com", hashed_password="first-password")
    )
    await db_session.flush()
    db_session.add(
        User(email="database-unique@example.com", hashed_password="second-password")
    )

    with pytest.raises(IntegrityError):
        await db_session.flush()

    await db_session.rollback()


@pytest.mark.asyncio(loop_scope="session")
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


@pytest.mark.asyncio(loop_scope="session")
async def test_login_failure_does_not_reveal_whether_email_exists(client: AsyncClient):
    """AUTH-004: unknown-email and wrong-password failures are identical."""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "known-login@example.com", "password": "password123"},
    )

    unknown_email = await client.post(
        "/api/v1/auth/login",
        json={"email": "unknown-login@example.com", "password": "password123"},
    )
    wrong_password = await client.post(
        "/api/v1/auth/login",
        json={"email": "known-login@example.com", "password": "wrong-password"},
    )

    assert unknown_email.status_code == wrong_password.status_code == 401
    assert (
        unknown_email.json()
        == wrong_password.json()
        == {"detail": "Invalid email or password"}
    )


@pytest.mark.asyncio(loop_scope="session")
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


@pytest.mark.asyncio(loop_scope="session")
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


@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_rotation_rejects_replay(
    client: AsyncClient,
    shared_redis,
):
    """AUTH-003: a refresh token is single-use after a successful rotation."""
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-rotation@example.com", "password": "password123"},
    )
    original_refresh_token = registration.json()["refresh_token"]

    first_refresh = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert first_refresh.status_code == 200
    assert first_refresh.json()["refresh_token"] != original_refresh_token

    replay = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": original_refresh_token},
    )

    assert replay.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_logout_revokes_access_and_refresh_session(
    client: AsyncClient,
    shared_redis,
):
    """AUTH-003: logout makes the current access and refresh session unusable."""
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "logout-revocation@example.com", "password": "password123"},
    )
    tokens = registration.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    logout_response = await client.post("/api/v1/auth/logout", headers=headers)
    access_after_logout = await client.get("/api/v1/auth/me", headers=headers)
    refresh_after_logout = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]},
    )

    assert logout_response.status_code == 200
    assert access_after_logout.status_code == 401
    assert refresh_after_logout.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_expired_access_token_is_rejected(client: AsyncClient):
    """AUTH-001: an expired access token cannot authenticate a request."""
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "expired@example.com", "password": "password123"},
    )
    valid_access_token = registration.json()["access_token"]
    current_user = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {valid_access_token}"},
    )
    user_id = current_user.json()["id"]
    expired_token = create_access_token(
        data={"sub": user_id},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    todos_response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert todos_response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_tampered_access_token_is_rejected(client: AsyncClient):
    """AUTH-005: a modified JWT signature cannot authenticate protected routes."""
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "tampered-token@example.com", "password": "password123"},
    )
    valid_token = registration.json()["access_token"]
    header, payload, signature = valid_token.split(".")
    replacement = "A" if signature[0] != "A" else "B"
    tampered_token = ".".join((header, payload, replacement + signature[1:]))
    headers = {"Authorization": f"Bearer {tampered_token}"}

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    todos_response = await client.get("/api/v1/todos", headers=headers)

    assert me_response.status_code == 401
    assert todos_response.status_code == 401


@pytest.mark.asyncio(loop_scope="session")
async def test_refresh_token_cannot_authenticate_access_endpoint(client: AsyncClient):
    """AUTH-002: access-only dependencies must reject refresh tokens."""
    registration = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh-as-access@example.com", "password": "password123"},
    )
    refresh_token = registration.json()["refresh_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    todos_response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )

    assert response.status_code == 401
    assert todos_response.status_code == 401
