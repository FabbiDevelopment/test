"""Authorization, data isolation, logic, and cache invalidation tests for Todos."""

import json
from unittest.mock import MagicMock
import uuid
import pytest
from httpx import AsyncClient


async def get_user_token(client: AsyncClient, email: str) -> str:
    """Helper to register and return access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


async def get_user_id(client: AsyncClient, token: str) -> str:
    """Helper to get current user ID."""
    response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    return response.json()["id"]


# ==========================================
# 1. IDOR & Cross-User Authorization Tests
# ==========================================

@pytest.mark.asyncio
async def test_user_a_cannot_read_user_b_todo(client: AsyncClient):
    """Test that User A cannot read User B's todo item (IDOR protection: 403 Forbidden)."""
    token_b = await get_user_token(client, "user_b_read@example.com")
    token_a = await get_user_token(client, "user_a_read@example.com")

    # User B creates a todo
    b_todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User B Secret Todo", "description": "Confidential data"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_todo_res.status_code == 201
    todo_id = b_todo_res.json()["id"]

    # User A attempts to GET User B's todo
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]


@pytest.mark.asyncio
async def test_user_a_cannot_update_user_b_todo(client: AsyncClient):
    """Test that User A cannot update User B's todo item (403 Forbidden)."""
    token_b = await get_user_token(client, "user_b_update@example.com")
    token_a = await get_user_token(client, "user_a_update@example.com")

    # User B creates a todo
    b_todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User B Original Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id = b_todo_res.json()["id"]

    # User A attempts to update User B's todo
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title by User A", "completed": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

    # Verify original todo remained unchanged
    verify_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert verify_res.json()["title"] == "User B Original Title"
    assert verify_res.json()["completed"] is False


@pytest.mark.asyncio
async def test_user_a_cannot_delete_user_b_todo(client: AsyncClient):
    """Test that User A cannot delete User B's todo item (403 Forbidden)."""
    token_b = await get_user_token(client, "user_b_delete@example.com")
    token_a = await get_user_token(client, "user_a_delete@example.com")

    # User B creates a todo
    b_todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo to Keep"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id = b_todo_res.json()["id"]

    # User A attempts to delete User B's todo
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403
    assert "Not authorized" in response.json()["detail"]

    # Verify todo still exists for User B
    verify_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert verify_res.status_code == 200


@pytest.mark.asyncio
async def test_user_todo_list_data_isolation(client: AsyncClient):
    """Test that User A's todo list does not expose any todos belonging to User B."""
    token_b = await get_user_token(client, "user_b_list@example.com")
    token_a = await get_user_token(client, "user_a_list@example.com")

    # User B creates 2 todos
    await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo 1"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo 2"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A creates 1 todo
    await client.post(
        "/api/v1/todos",
        json={"title": "User A Sole Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User A lists todos
    res_a = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    items_a = res_a.json()["items"]
    titles_a = [item["title"] for item in items_a]

    assert "User A Sole Todo" in titles_a
    assert "User B Todo 1" not in titles_a
    assert "User B Todo 2" not in titles_a
    assert res_a.json()["total"] == 1


# ==========================================
# 2. Todo Logic & Edge Cases Tests
# ==========================================

@pytest.mark.asyncio
async def test_boolean_toggle_true_to_false(client: AsyncClient):
    """Test updating completed boolean from False -> True -> False."""
    token = await get_user_token(client, "toggle_bool@example.com")

    # 1. Create todo (default completed is False)
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    assert create_res.json()["completed"] is False

    # 2. Update to True
    res_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_true.status_code == 200
    assert res_true.json()["completed"] is True

    # 3. Update back to False (critical regression check for falsy value handling)
    res_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_false.status_code == 200
    assert res_false.json()["completed"] is False

    # 4. Confirm in database via GET
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test that updating only title preserves existing description (exclude_unset)."""
    token = await get_user_token(client, "partial_update@example.com")

    # Create todo with description
    create_res = await client.post(
        "/api/v1/todos",
        json={
            "title": "Initial Title",
            "description": "Crucial description that must not be wiped out",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    # Update only title (omitting description entirely)
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    assert update_res.json()["title"] == "Updated Title Only"
    assert update_res.json()["description"] == "Crucial description that must not be wiped out"

    # Confirm via GET
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.json()["description"] == "Crucial description that must not be wiped out"


@pytest.mark.asyncio
async def test_update_nonexistent_todo_returns_404(client: AsyncClient):
    """Test updating a non-existent todo returns 404."""
    token = await get_user_token(client, "notfound_update@example.com")
    random_id = str(uuid.uuid4())

    response = await client.put(
        f"/api/v1/todos/{random_id}",
        json={"title": "Does Not Exist"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "Todo not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_delete_nonexistent_todo_returns_404(client: AsyncClient):
    """Test deleting a non-existent todo returns 404."""
    token = await get_user_token(client, "notfound_delete@example.com")
    random_id = str(uuid.uuid4())

    response = await client.delete(
        f"/api/v1/todos/{random_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 404
    assert "Todo not found" in response.json()["detail"]


# ==========================================
# 3. Cache Invalidation Tests
# ==========================================

@pytest.mark.asyncio
async def test_cache_invalidated_on_create_todo(client: AsyncClient, mock_redis_client: MagicMock):
    """Test that creating a new todo invalidates user's cached todo list."""
    token = await get_user_token(client, "cache_create@example.com")
    user_id = await get_user_id(client, token)

    mock_redis_client.delete_pattern.reset_mock()

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Invalidation Create"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201

    # Verify delete_pattern was called with user-specific pattern
    mock_redis_client.delete_pattern.assert_called_once_with(f"todos:user:{user_id}:*")


@pytest.mark.asyncio
async def test_cache_invalidated_on_update_todo(client: AsyncClient, mock_redis_client: MagicMock):
    """Test that updating a todo invalidates user's cached todo list."""
    token = await get_user_token(client, "cache_update@example.com")
    user_id = await get_user_id(client, token)

    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Invalidation Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    mock_redis_client.delete_pattern.reset_mock()

    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200

    mock_redis_client.delete_pattern.assert_called_once_with(f"todos:user:{user_id}:*")


@pytest.mark.asyncio
async def test_cache_invalidated_on_delete_todo(client: AsyncClient, mock_redis_client: MagicMock):
    """Test that deleting a todo invalidates user's cached todo list."""
    token = await get_user_token(client, "cache_delete@example.com")
    user_id = await get_user_id(client, token)

    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Invalidation Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    mock_redis_client.delete_pattern.reset_mock()

    delete_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_res.status_code == 204

    mock_redis_client.delete_pattern.assert_called_once_with(f"todos:user:{user_id}:*")


@pytest.mark.asyncio
async def test_list_todos_cache_hit(client: AsyncClient, mock_redis_client: MagicMock):
    """Test that list_todos returns cached response without querying database on cache hit."""
    token = await get_user_token(client, "cache_hit@example.com")

    cached_payload = {
        "items": [
            {
                "id": str(uuid.uuid4()),
                "title": "Cached Todo Item",
                "description": "Retrieved directly from Redis",
                "completed": False,
                "user_id": str(uuid.uuid4()),
                "created_at": "2026-09-16T00:00:00Z",
                "updated_at": "2026-09-16T00:00:00Z",
                "user_email": "cache_hit@example.com",
            }
        ],
        "total": 1,
        "page": 1,
        "size": 20,
    }
    mock_redis_client.get.return_value = json.dumps(cached_payload)

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Cached Todo Item"
