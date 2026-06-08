"""Tests for remaining assessment bugs (Bugs #2, #3, #4, #5)."""

import pytest
from httpx import AsyncClient
from unittest.mock import MagicMock

from app.core.security import create_refresh_token, create_access_token


@pytest.mark.asyncio
async def test_bug_2_idor_protection(client: AsyncClient):
    """Test that User B cannot access, update, or delete User A's todo."""
    # 1. Register and login User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "usera@example.com", "password": "password123"},
    )
    token_a = res_a.json()["access_token"]

    # 2. User A creates a Todo
    todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo", "description": "Private todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = todo_res.json()["id"]

    # 3. Register and login User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "userb@example.com", "password": "password123"},
    )
    token_b = res_b.json()["access_token"]

    # 4. User B attempts to GET User A's Todo -> 403 Forbidden
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 403

    # 5. User B attempts to PUT User A's Todo -> 403 Forbidden
    put_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_res.status_code == 403

    # 6. User B attempts to DELETE User A's Todo -> 403 Forbidden
    del_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 403

    # 7. User A can still access and modify their own Todo
    get_a_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_a_res.status_code == 200


@pytest.mark.asyncio
async def test_bug_3_cache_isolation_and_invalidation(client: AsyncClient):
    """Test that Redis cache keys are user-scoped and invalidated correctly."""
    # 1. Register User A
    res_a = await client.post(
        "/api/v1/auth/register",
        json={"email": "cache_a@example.com", "password": "password123"},
    )
    token_a = res_a.json()["access_token"]

    # 2. Register User B
    res_b = await client.post(
        "/api/v1/auth/register",
        json={"email": "cache_b@example.com", "password": "password123"},
    )
    token_b = res_b.json()["access_token"]

    from app.api.deps import get_redis
    from app.main import app

    mock_redis = app.dependency_overrides[get_redis]()
    app.dependency_overrides[get_redis] = lambda: mock_redis

    # GET request by User A
    mock_redis.get.reset_mock()
    await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    mock_redis.get.assert_called_once()
    key_a = mock_redis.get.call_args[0][0]

    # GET request by User B
    mock_redis.get.reset_mock()
    await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    mock_redis.get.assert_called_once()
    key_b = mock_redis.get.call_args[0][0]

    # Keys must be different because of user_id scoping
    assert key_a != key_b
    assert "todos:list:" in key_a
    assert "todos:list:" in key_b

    # Verify invalidation on mutation (POST)
    mock_redis.delete_pattern.reset_mock()
    await client.post(
        "/api/v1/todos",
        json={"title": "New Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    mock_redis.delete_pattern.assert_called_once()
    assert "todos:list:" in mock_redis.delete_pattern.call_args[0][0]


@pytest.mark.asyncio
async def test_bug_4_refresh_token_rejected_on_access_routes(client: AsyncClient):
    """Test that refresh tokens are rejected on endpoints requiring access tokens."""
    # 1. Register to get tokens
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "token_type@example.com", "password": "password123"},
    )
    data = res.json()
    access_token = data["access_token"]
    refresh_token = data["refresh_token"]

    # 2. Access token should work on GET /me
    me_access = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_access.status_code == 200

    # 3. Refresh token should be rejected on GET /me (returns 401)
    me_refresh = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {refresh_token}"},
    )
    assert me_refresh.status_code == 401
    assert "token type" in me_refresh.json()["detail"].lower()


@pytest.mark.asyncio
async def test_bug_5_todo_toggle_completed(client: AsyncClient):
    """Test that completed state of todo can be updated to both True and False."""
    # 1. Register and login User
    res = await client.post(
        "/api/v1/auth/register",
        json={"email": "toggle@example.com", "password": "password123"},
    )
    token = res.json()["access_token"]

    # 2. Create Todo (completed defaults to False)
    todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo = todo_res.json()
    todo_id = todo["id"]
    assert todo["completed"] is False

    # 3. Toggle completed to True
    put_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_true.status_code == 200
    assert put_true.json()["completed"] is True

    # 4. Toggle completed back to False (this is where the bug was)
    put_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_false.status_code == 200
    assert put_false.json()["completed"] is False
