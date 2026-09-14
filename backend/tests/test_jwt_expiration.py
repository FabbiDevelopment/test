"""Tests for JWT token expiration and security."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from httpx import AsyncClient

from app.core.security import (
    TokenError,
    create_access_token,
    create_refresh_token,
    verify_token,
)


class TestVerifyTokenExpiration:
    """Unit tests for verify_token expiration handling."""

    def test_valid_token_within_expiry(self):
        """A token within its expiry window should be accepted."""
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(minutes=10),
        )
        result = verify_token(token)
        assert isinstance(result, dict)
        assert result["sub"] == "user-123"
        assert result["type"] == "access"

    def test_expired_token_is_rejected(self):
        """A token that has already expired should return a TokenError."""
        token = create_access_token(
            data={"sub": "user-123"},
            expires_delta=timedelta(seconds=-1),  # already expired
        )
        result = verify_token(token)
        assert isinstance(result, TokenError)
        assert result.reason == "Token has expired"

    def test_valid_refresh_token_within_expiry(self):
        """A refresh token within its expiry window should be accepted."""
        token = create_refresh_token(
            data={"sub": "user-456"},
            expires_delta=timedelta(days=7),
        )
        result = verify_token(token)
        assert isinstance(result, dict)
        assert result["sub"] == "user-456"
        assert result["type"] == "refresh"

    def test_expired_refresh_token_is_rejected(self):
        """An expired refresh token should return a TokenError."""
        token = create_refresh_token(
            data={"sub": "user-456"},
            expires_delta=timedelta(seconds=-1),
        )
        result = verify_token(token)
        assert isinstance(result, TokenError)
        assert result.reason == "Token has expired"

    def test_invalid_token_is_rejected(self):
        """A completely invalid token string should return a TokenError."""
        result = verify_token("not-a-valid-jwt")
        assert isinstance(result, TokenError)
        assert result.reason == "Invalid token"

    def test_tampered_token_is_rejected(self):
        """A token with a tampered payload should return a TokenError."""
        token = create_access_token(data={"sub": "user-123"})
        # Tamper with the token by modifying the payload segment
        parts = token.split(".")
        parts[1] = parts[1] + "tampered"
        tampered_token = ".".join(parts)
        result = verify_token(tampered_token)
        assert isinstance(result, TokenError)

    def test_default_access_token_expiry_is_set(self):
        """Access tokens should include 'exp' claim by default."""
        token = create_access_token(data={"sub": "user-789"})
        result = verify_token(token)
        assert isinstance(result, dict)
        assert "exp" in result

    def test_default_refresh_token_expiry_is_set(self):
        """Refresh tokens should include 'exp' and 'jti' claims."""
        token = create_refresh_token(data={"sub": "user-789"})
        result = verify_token(token)
        assert isinstance(result, dict)
        assert "exp" in result
        assert "jti" in result


@pytest.mark.asyncio
async def test_expired_access_token_returns_401(client: AsyncClient):
    """An expired access token should result in HTTP 401 on protected endpoints."""
    expired_token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_valid_access_token_is_accepted(client: AsyncClient):
    """A freshly created access token should work for authentication."""
    # Register to create a real user, then use the returned token
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "expiry_test@example.com", "password": "password123"},
    )
    token = reg_response.json()["access_token"]

    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["email"] == "expiry_test@example.com"


@pytest.mark.asyncio
async def test_expired_refresh_token_returns_401(client: AsyncClient):
    """An expired refresh token should result in HTTP 401 on the /refresh endpoint."""
    expired_refresh = create_refresh_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-1),
    )

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_refresh},
    )
    assert response.status_code == 401
    assert "expired" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_valid_refresh_token_returns_new_tokens(client: AsyncClient):
    """A valid refresh token should return a new access + refresh token pair."""
    # Register to get valid tokens
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": "refresh_test@example.com", "password": "password123"},
    )
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
