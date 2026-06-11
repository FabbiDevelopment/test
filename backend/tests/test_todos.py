"""Todo tests."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


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


# ── NEW SECURITY TESTS ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_cannot_read_other_users_todo(client: AsyncClient):
    """User A must not be able to read User B's todo (ownership enforcement)."""
    token_a = await get_auth_token(client, "user_a@example.com")
    token_b = await get_auth_token(client, "user_b@example.com")

    # User A creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User A's secret todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]

    # User B tries to read it — must get 403
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio
async def test_cannot_update_other_users_todo(client: AsyncClient):
    """User A must not be able to update User B's todo."""
    token_a = await get_auth_token(client, "upd_a@example.com")
    token_b = await get_auth_token(client, "upd_b@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Owner's todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hijacked title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio
async def test_cannot_delete_other_users_todo(client: AsyncClient):
    """User A must not be able to delete User B's todo."""
    token_a = await get_auth_token(client, "del_a@example.com")
    token_b = await get_auth_token(client, "del_b@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Protected todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_response.json()["id"]

    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403, (
        f"Expected 403, got {response.status_code}: {response.text}"
    )


@pytest.mark.asyncio
async def test_todo_list_isolation_between_users(client: AsyncClient):
    """User A must only see their own todos, not User B's."""
    token_a = await get_auth_token(client, "iso_a@example.com")
    token_b = await get_auth_token(client, "iso_b@example.com")

    # User B creates a todo
    await client.post(
        "/api/v1/todos",
        json={"title": "User B only"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A should see an empty list (zero todos)
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0, "User A should not see User B's todos"


@pytest.mark.asyncio
async def test_update_todo_partial_fields(client: AsyncClient):
    """Partial update (only completed) should not wipe title."""
    token = await get_auth_token(client, "partial@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Send only `completed`, title should be preserved
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is True
    assert data["title"] == "Original Title", "Title must not be wiped on partial update"


@pytest.mark.asyncio
async def test_update_completed_false_works(client: AsyncClient):
    """Regression: setting completed=False must work (old code skipped falsy values).

    The original bug: `if todo_data.completed: todo.completed = ...` would never
    execute when completed=False, making it impossible to un-complete a todo.
    """
    token = await get_auth_token(client, "uncomplete@example.com")

    # Create already-completed todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Already done", "description": None},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Mark as completed first
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Now un-complete it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is False, (
        "completed=False must be persisted (regression for the falsy-value skip bug)"
    )


@pytest.mark.asyncio
async def test_cache_keys_are_user_scoped(client: AsyncClient):
    """Cache key must be scoped per-user so users never receive each other's data.

    This test verifies that two users get their own isolated todo lists.
    We rely on the HTTP layer since Redis is mocked in tests — the isolation is
    proven by confirming user A sees zero todos when only user B has created any.
    """
    token_a = await get_auth_token(client, "cache_a@example.com")
    token_b = await get_auth_token(client, "cache_b@example.com")

    # User B creates a todo
    await client.post(
        "/api/v1/todos",
        json={"title": "User B's todo — should NOT appear for A"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    # User A sees their own empty list
    res_a = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert res_a.status_code == 200
    assert res_a.json()["total"] == 0, (
        "User A must not see User B's todos — cache keys are NOT user-scoped"
    )

    # User B sees exactly 1 todo
    res_b = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res_b.status_code == 200
    assert res_b.json()["total"] == 1
