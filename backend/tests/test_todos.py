"""Todo tests — Tier 2A.

Covers:
- Happy-path CRUD
- Scenario 1: Authorization boundary — User A cannot read/update/delete User B's todos
- Scenario 2: Boolean toggle — completed can be set back to False
- Scenario 3: Partial update — updating title does NOT erase description
- Scenario 4: Cache invalidation — redis.delete_pattern called on create/update/delete
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient

from app.api.deps import get_redis


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def register_and_token(client: AsyncClient, email: str) -> str:
    """Register a new user and return the access token."""
    resp = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Test@pass1"},
    )
    assert resp.status_code == 201, f"Registration failed: {resp.json()}"
    return resp.json()["access_token"]


async def create_todo(
    client: AsyncClient,
    token: str,
    title: str = "My Todo",
    description: str | None = "Some description",
) -> dict:
    """Create a todo and return the response JSON."""
    payload = {"title": title}
    if description is not None:
        payload["description"] = description
    resp = await client.post(
        "/api/v1/todos",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Create todo failed: {resp.json()}"
    return resp.json()


# ---------------------------------------------------------------------------
# Happy-path CRUD
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_todo_success(client: AsyncClient):
    """Creating a todo with title and description returns 201."""
    token = await register_and_token(client, "create_todo@example.com")
    data = await create_todo(client, token, "Buy milk", "2 litres, full-fat")
    assert data["title"] == "Buy milk"
    assert data["description"] == "2 litres, full-fat"
    assert data["completed"] is False
    assert "id" in data


@pytest.mark.asyncio
async def test_list_todos_returns_only_own_todos(client: AsyncClient):
    """GET /todos returns only the authenticated user's todos."""
    token_a = await register_and_token(client, "list_a@example.com")
    token_b = await register_and_token(client, "list_b@example.com")

    await create_todo(client, token_a, "User A's todo")
    await create_todo(client, token_b, "User B's todo")

    resp = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["title"] != "User B's todo" for item in items)
    assert any(item["title"] == "User A's todo" for item in items)


@pytest.mark.asyncio
async def test_get_own_todo_success(client: AsyncClient):
    """GET /todos/{id} returns the todo for its owner."""
    token = await register_and_token(client, "get_own@example.com")
    todo = await create_todo(client, token, "Owned todo")

    resp = await client.get(
        f"/api/v1/todos/{todo['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["id"] == todo["id"]


@pytest.mark.asyncio
async def test_delete_own_todo_success(client: AsyncClient):
    """DELETE /todos/{id} by the owner returns 204."""
    token = await register_and_token(client, "del_own@example.com")
    todo = await create_todo(client, token, "Delete me")

    resp = await client.delete(
        f"/api/v1/todos/{todo['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_get_deleted_todo_returns_404(client: AsyncClient):
    """GET /todos/{id} after deletion returns 404."""
    token = await register_and_token(client, "get_deleted@example.com")
    todo = await create_todo(client, token, "Gone soon")
    todo_id = todo["id"]

    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Scenario 1 — Authorization boundary: User A ≠ User B
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_todo(client: AsyncClient):
    """User B cannot GET a todo that belongs to User A.

    Expected: 403 Forbidden (not 200 or 404).
    """
    token_a = await register_and_token(client, "read_a@example.com")
    token_b = await register_and_token(client, "read_b@example.com")

    todo_a = await create_todo(client, token_a, "A's private note")

    # User B tries to read User A's todo
    resp = await client.get(
        f"/api/v1/todos/{todo_a['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, (
        "User B must NOT be able to read User A's todo — expected 403, "
        f"got {resp.status_code}: {resp.json()}"
    )


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_todo(client: AsyncClient):
    """User B cannot PUT a todo that belongs to User A.

    Expected: 403 Forbidden.
    """
    token_a = await register_and_token(client, "upd_a@example.com")
    token_b = await register_and_token(client, "upd_b@example.com")

    todo_a = await create_todo(client, token_a, "A's task")

    resp = await client.put(
        f"/api/v1/todos/{todo_a['id']}",
        json={"title": "Hijacked by B"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, (
        f"User B must NOT update User A's todo — got {resp.status_code}: {resp.json()}"
    )

    # Verify the title is unchanged in the DB
    get_resp = await client.get(
        f"/api/v1/todos/{todo_a['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_resp.json()["title"] == "A's task"


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_todo(client: AsyncClient):
    """User B cannot DELETE a todo that belongs to User A.

    Expected: 403 Forbidden.
    """
    token_a = await register_and_token(client, "delab_a@example.com")
    token_b = await register_and_token(client, "delab_b@example.com")

    todo_a = await create_todo(client, token_a, "Don't delete me")

    resp = await client.delete(
        f"/api/v1/todos/{todo_a['id']}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp.status_code == 403, (
        f"User B must NOT delete User A's todo — got {resp.status_code}: {resp.json()}"
    )

    # Todo must still exist for User A
    get_resp = await client.get(
        f"/api/v1/todos/{todo_a['id']}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_resp.status_code == 200


# ---------------------------------------------------------------------------
# Scenario 2 — Boolean toggle: completed true → false persists correctly
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_completed_true_then_false(client: AsyncClient):
    """Setting completed=True, then completed=False, must persist False.

    This tests the bug where `if todo_data.completed:` skipped
    falsy values, making it impossible to un-complete a todo.
    """
    token = await register_and_token(client, "toggle@example.com")
    todo = await create_todo(client, token, "Toggle me")
    todo_id = todo["id"]
    assert todo["completed"] is False

    # Mark as completed
    resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["completed"] is True

    # Un-complete (set back to False)
    resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    assert resp.json()["completed"] is False, (
        "completed must persist as False — the boolean guard bug would keep it True"
    )

    # Confirm persisted by re-fetching
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.json()["completed"] is False


@pytest.mark.asyncio
async def test_completed_defaults_to_false_on_create(client: AsyncClient):
    """Newly created todos must have completed=False."""
    token = await register_and_token(client, "default_false@example.com")
    todo = await create_todo(client, token, "Brand new")
    assert todo["completed"] is False


# ---------------------------------------------------------------------------
# Scenario 3 — Partial update: updating title does NOT erase description
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_update_title_preserves_description(client: AsyncClient):
    """Sending only title in a PUT must not set description to None.

    The backend reads the whole model_dump() which includes description=None
    when omitted; the update logic must not overwrite the existing description
    unless the client explicitly sends a new value.
    """
    token = await register_and_token(client, "partial@example.com")
    todo = await create_todo(client, token, "Original title", "Keep this description")
    todo_id = todo["id"]
    assert todo["description"] == "Keep this description"

    # Update only the title
    resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "New title"
    assert data["description"] == "Keep this description", (
        "Description must not be erased when only title is updated"
    )


@pytest.mark.asyncio
async def test_partial_update_description_preserves_title(client: AsyncClient):
    """Sending only description must not erase the title."""
    token = await register_and_token(client, "partial2@example.com")
    todo = await create_todo(client, token, "Keep this title", "Original desc")
    todo_id = todo["id"]

    resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"description": "New description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Keep this title"
    assert data["description"] == "New description"


@pytest.mark.asyncio
async def test_update_only_completed_preserves_title_and_description(client: AsyncClient):
    """Sending only completed must not touch title or description."""
    token = await register_and_token(client, "partial3@example.com")
    todo = await create_todo(client, token, "Stable title", "Stable description")
    todo_id = todo["id"]

    resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Stable title"
    assert data["description"] == "Stable description"
    assert data["completed"] is True


# ---------------------------------------------------------------------------
# Scenario 4 — Cache invalidation: redis.delete_pattern called on mutations
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_todo_invalidates_cache(client: AsyncClient):
    """Creating a todo must call redis.delete_pattern to bust the list cache."""
    from app.main import app as fastapi_app

    token = await register_and_token(client, "cache_create@example.com")

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.delete_pattern = AsyncMock()

    fastapi_app.dependency_overrides[get_redis] = lambda: mock_redis

    resp = await client.post(
        "/api/v1/todos",
        json={"title": "Cache buster"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201

    mock_redis.delete_pattern.assert_called_once()
    pattern_arg = mock_redis.delete_pattern.call_args[0][0]
    assert "todos:list:" in pattern_arg, (
        f"delete_pattern should target todos:list:*, got: {pattern_arg}"
    )


@pytest.mark.asyncio
async def test_update_todo_invalidates_cache(client: AsyncClient):
    """Updating a todo must call redis.delete_pattern."""
    from app.main import app as fastapi_app

    token = await register_and_token(client, "cache_update@example.com")
    todo = await create_todo(client, token, "To be updated")

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.delete_pattern = AsyncMock()

    fastapi_app.dependency_overrides[get_redis] = lambda: mock_redis

    resp = await client.put(
        f"/api/v1/todos/{todo['id']}",
        json={"title": "Updated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200
    mock_redis.delete_pattern.assert_called_once()


@pytest.mark.asyncio
async def test_delete_todo_invalidates_cache(client: AsyncClient):
    """Deleting a todo must call redis.delete_pattern."""
    from app.main import app as fastapi_app

    token = await register_and_token(client, "cache_delete@example.com")
    todo = await create_todo(client, token, "To be deleted")

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    mock_redis.delete_pattern = AsyncMock()

    fastapi_app.dependency_overrides[get_redis] = lambda: mock_redis

    resp = await client.delete(
        f"/api/v1/todos/{todo['id']}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 204
    mock_redis.delete_pattern.assert_called_once()


@pytest.mark.asyncio
async def test_list_todos_uses_user_scoped_cache_key(client: AsyncClient):
    """GET /todos must write cache with a key scoped to the user ID, not global.

    If two different users fetch their list, redis.set must be called with
    different cache keys containing each user's ID.
    """
    from app.main import app as fastapi_app

    token_a = await register_and_token(client, "cache_scope_a@example.com")
    token_b = await register_and_token(client, "cache_scope_b@example.com")

    await create_todo(client, token_a, "A's todo")
    await create_todo(client, token_b, "B's todo")

    cache_keys: list[str] = []

    mock_redis = MagicMock()
    mock_redis.get = AsyncMock(return_value=None)
    mock_redis.delete_pattern = AsyncMock()

    async def capture_set(key: str, value: str, ex=None):
        cache_keys.append(key)

    mock_redis.set = AsyncMock(side_effect=capture_set)

    fastapi_app.dependency_overrides[get_redis] = lambda: mock_redis

    # User A fetches
    resp_a = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 200

    # User B fetches
    resp_b = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200

    # Must have 2 distinct cache keys
    assert len(cache_keys) == 2, f"Expected 2 cache writes, got {len(cache_keys)}: {cache_keys}"
    assert cache_keys[0] != cache_keys[1], (
        "Cache keys for two different users must differ — "
        f"both were: {cache_keys[0]}"
    )
    assert all("todos:list:" in k for k in cache_keys), (
        f"Cache keys must contain 'todos:list:' prefix: {cache_keys}"
    )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_todo_with_no_description(client: AsyncClient):
    """Creating a todo without description stores None."""
    token = await register_and_token(client, "nodesc@example.com")
    resp = await client.post(
        "/api/v1/todos",
        json={"title": "No description todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201
    assert resp.json()["description"] is None


@pytest.mark.asyncio
async def test_todo_requires_title(client: AsyncClient):
    """Creating a todo without title returns 422."""
    token = await register_and_token(client, "notitle@example.com")
    resp = await client.post(
        "/api/v1/todos",
        json={"description": "No title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_get_nonexistent_todo_returns_404(client: AsyncClient):
    """GET /todos/{id} with a valid but nonexistent UUID returns 404."""
    token = await register_and_token(client, "no_todo@example.com")
    fake_id = "00000000-0000-0000-0000-000000000999"
    resp = await client.get(
        f"/api/v1/todos/{fake_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthenticated_cannot_access_todos(client: AsyncClient):
    """Requests without token cannot list or create todos."""
    resp = await client.get("/api/v1/todos")
    assert resp.status_code in (401, 403)

    resp = await client.post("/api/v1/todos", json={"title": "Sneaky"})
    assert resp.status_code in (401, 403)
