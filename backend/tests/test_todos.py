"""Todo tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import register_user


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


# ── Existing tests ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await get_auth_token(client, "create@example.com")

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Test Todo", "description": "A test todo item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test todo item"
    assert data["completed"] is False


@pytest.mark.asyncio
async def test_get_todos(client: AsyncClient):
    """Test getting todo list."""
    token = await get_auth_token(client, "list@example.com")

    # Create a todo first
    await client.post(
        "/api/v1/todos",
        json={"title": "List Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_update_todo(client: AsyncClient):
    """Test updating a todo."""
    token = await get_auth_token(client, "update@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_get_single_todo(client: AsyncClient):
    """Test getting a single todo by ID."""
    token = await get_auth_token(client, "single@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Single Todo", "description": "Get me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Todo"


# ── New Tier 2 tests ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_cannot_read_other_users_todo(client: AsyncClient):
    """Tier 2 — Bug #3 regression: authorization boundary (GET).

    User A creates a todo. User B must receive 403 when trying to read it.
    Verifies ownership enforcement on the GET /{todo_id} endpoint.
    """
    token_a = await get_auth_token(client, "owner_read_a@example.com")
    token_b = await get_auth_token(client, "attacker_read_b@example.com")

    # User A creates a todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B tries to read it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403, (
        "User B should not be able to read User A's todo. "
        "Expected 403 Forbidden, but got a different status."
    )


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_todo(client: AsyncClient):
    """Tier 2 — Bug #3 regression: authorization boundary (PUT).

    User A creates a todo. User B must receive 403 when trying to update it.
    """
    token_a = await get_auth_token(client, "owner_update_a@example.com")
    token_b = await get_auth_token(client, "attacker_update_b@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hijacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403, (
        "User B should not be able to update User A's todo. "
        "Expected 403 Forbidden."
    )


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_todo(client: AsyncClient):
    """Tier 2 — Bug #3 regression: authorization boundary (DELETE).

    User A creates a todo. User B must receive 403 when trying to delete it.
    """
    token_a = await get_auth_token(client, "owner_delete_a@example.com")
    token_b = await get_auth_token(client, "attacker_delete_b@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo to Delete"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )

    assert response.status_code == 403, (
        "User B should not be able to delete User A's todo. "
        "Expected 403 Forbidden."
    )


@pytest.mark.asyncio
async def test_toggle_completed_from_true_to_false(client: AsyncClient):
    """Tier 2 — Bug #4 regression: completed toggle must persist false value.

    Creates a todo, marks it completed, then un-completes it. The final state
    must be completed=False. The bug was that `if todo_data.completed:` skipped
    False values — making it impossible to un-complete a todo.
    """
    token = await get_auth_token(client, "toggle@example.com")

    # Create todo (completed=False by default)
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]
    assert create_resp.json()["completed"] is False

    # Mark as completed
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Now un-complete it (this was the broken path)
    uncomplete_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert uncomplete_resp.status_code == 200
    assert uncomplete_resp.json()["completed"] is False, (
        "completed should be False after sending completed=False. "
        "If this fails, the truthy-check bug is still present."
    )

    # Confirm by fetching the todo directly
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Tier 2 — Partial update: updating title must NOT erase description.

    Creates a todo with both title and description. Updates only the title.
    The description must remain unchanged.
    """
    token = await get_auth_token(client, "partial@example.com")

    # Create todo with description
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Important description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]

    # Update only the title
    update_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200

    # Fetch and verify description was preserved
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = get_resp.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Important description", (
        "Description should not be erased when only title is updated."
    )


@pytest.mark.asyncio
async def test_cache_invalidated_after_create(client: AsyncClient):
    """Tier 2 — Bug #5 regression: Redis cache must be invalidated after create.

    After creating a todo, the mock redis.delete_pattern must be called
    with the user-scoped cache key pattern. This ensures the next GET /todos
    fetches fresh data instead of stale cached results.
    """
    from app.api.deps import get_redis
    from unittest.mock import AsyncMock, MagicMock

    # Create a fresh mock to track calls for this specific test
    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.delete_pattern = AsyncMock(return_value=1)
    mock_redis.set_blacklist = AsyncMock()
    mock_redis.is_blacklisted = AsyncMock(return_value=False)

    # Override redis for this test
    from app.main import app
    app.dependency_overrides[get_redis] = lambda: mock_redis

    try:
        token = await get_auth_token(client, "cache_test@example.com")

        await client.post(
            "/api/v1/todos",
            json={"title": "Cache Test Todo"},
            headers={"Authorization": f"Bearer {token}"},
        )

        # Verify delete_pattern was called (cache invalidation happened)
        assert mock_redis.delete_pattern.called, (
            "redis.delete_pattern should be called after creating a todo "
            "to invalidate the user's todo list cache."
        )
        # Verify the pattern is user-scoped (not the old global key)
        call_args = mock_redis.delete_pattern.call_args[0][0]
        assert "todos:list:" in call_args, (
            f"Cache key pattern should be user-scoped. Got: {call_args}"
        )
    finally:
        # Restore the original override
        from tests.conftest import override_get_redis
        app.dependency_overrides[get_redis] = override_get_redis
