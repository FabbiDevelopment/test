"""Security and Authorization Boundary tests for Tier 2 Requirements."""

from datetime import timedelta

import pytest
from httpx import AsyncClient

from app.core.config import settings
from app.core.security import create_access_token


async def get_auth_token(client: AsyncClient, email: str) -> str:
    """Helper function to register and return access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password@123"},
    )
    return response.json()["access_token"]


# Scenario 1: Expired or tampered JWT access token rejection
@pytest.mark.asyncio
async def test_expired_jwt_token_rejected(client: AsyncClient):
    """Test that an expired JWT token is rejected with HTTP 401."""
    expired_token = create_access_token(
        data={"sub": "00000000-0000-0000-0000-000000000001"},
        expires_delta=timedelta(seconds=-10),
    )
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_jwt_token_rejected(client: AsyncClient):
    """Test that a tampered JWT token is rejected with HTTP 401."""
    token = create_access_token(data={"sub": "00000000-0000-0000-0000-000000000001"})
    tampered_token = token[:-5] + "XXXXX"
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == 401


# Scenario 2: Authorization boundary - User A cannot read, update, or delete User B's todos
@pytest.mark.asyncio
async def test_user_cannot_access_other_user_todo(client: AsyncClient):
    """Test IDOR boundary enforcement across GET, PUT, DELETE endpoints."""
    token_a = await get_auth_token(client, "usera_boundary@example.com")
    token_b = await get_auth_token(client, "userb_boundary@example.com")

    # User A creates a todo
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo", "description": "Secret"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_res.status_code == 201
    todo_id = create_res.json()["id"]

    # User B tries to read User A's todo -> 404
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 404

    # User B tries to update User A's todo -> 404
    put_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_res.status_code == 404

    # User B tries to delete User A's todo -> 404
    delete_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert delete_res.status_code == 404

    # User A can still access their own todo
    get_a_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_a_res.status_code == 200
    assert get_a_res.json()["title"] == "User A Private Todo"


# Scenario 3: Boolean toggle - Updating completed from true back to false persists correctly
@pytest.mark.asyncio
async def test_toggle_completed_true_to_false_persists(client: AsyncClient):
    """Test toggling completed from True back to False persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # 1. Create todo (default completed = False)
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    assert create_res.json()["completed"] is False

    # 2. Update completed = True
    put_true_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_true_res.status_code == 200
    assert put_true_res.json()["completed"] is True

    # 3. Update completed back to False
    put_false_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_false_res.status_code == 200
    assert put_false_res.json()["completed"] is False

    # 4. Verify GET returns completed = False
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.json()["completed"] is False


# Scenario 4: Incomplete partial update - Updating title does not erase description
@pytest.mark.asyncio
async def test_partial_update_title_preserves_description(client: AsyncClient):
    """Test updating title in partial update preserves existing description."""
    token = await get_auth_token(client, "partial@example.com")

    # Create todo with description
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Original Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    # Update only title
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "Updated Title Only"
    assert data["description"] == "Original Description"


# Scenario 5: Cache invalidation - Creating, updating, or deleting a todo invalidates Redis cache
@pytest.mark.asyncio
async def test_cache_invalidation_on_todo_mutations(client: AsyncClient):
    """Test that creating, updating, or deleting a todo triggers cache invalidation."""
    from app.api.deps import get_redis
    from app.main import app

    redis_mock = app.dependency_overrides[get_redis]()

    token = await get_auth_token(client, "cache_invalidation@example.com")

    # Create todo -> should trigger delete_pattern
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Test Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    redis_mock.delete_pattern.assert_called()

    # Reset mock call count
    redis_mock.delete_pattern.reset_mock()

    # Update todo -> should trigger delete_pattern
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Cache Test Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    redis_mock.delete_pattern.assert_called()

    # Reset mock call count
    redis_mock.delete_pattern.reset_mock()

    # Delete todo -> should trigger delete_pattern
    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    redis_mock.delete_pattern.assert_called()
