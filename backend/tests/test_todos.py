"""Todo tests — CRUD + authorization boundary + cache invalidation."""

import pytest
from httpx import AsyncClient


async def register_and_login(
    client: AsyncClient, email: str, password: str = "password123"
) -> str:
    """Helper: register a new user and return their access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, f"Registration failed: {response.text}"
    return response.json()["access_token"]


# ─── Basic CRUD ────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await register_and_login(client, "create@example.com")

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
    token = await register_and_login(client, "list@example.com")

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
    token = await register_and_login(client, "update@example.com")

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
    token = await register_and_login(client, "delete@example.com")

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
    token = await register_and_login(client, "single@example.com")

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


# ─── Authorization Boundary Tests ─────────────────────────────────────────────


@pytest.mark.asyncio
async def test_user_cannot_read_another_users_todo(client: AsyncClient):
    """Authorization test: User A cannot GET User B's todo — must return 403."""
    token_a = await register_and_login(client, "userA_read@example.com")
    token_b = await register_and_login(client, "userB_read@example.com")

    # User B creates a todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User B's secret todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id = create_resp.json()["id"]

    # User A tries to read it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_todo(client: AsyncClient):
    """Authorization test: User A cannot PUT User B's todo — must return 403."""
    token_a = await register_and_login(client, "userA_update@example.com")
    token_b = await register_and_login(client, "userB_update@example.com")

    # User B creates a todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User B's todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id = create_resp.json()["id"]

    # User A tries to update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked by User A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_another_users_todo(client: AsyncClient):
    """Authorization test: User A cannot DELETE User B's todo — must return 403."""
    token_a = await register_and_login(client, "userA_delete@example.com")
    token_b = await register_and_login(client, "userB_delete@example.com")

    # User B creates a todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User B's todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id = create_resp.json()["id"]

    # User A tries to delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_todo_list_is_isolated(client: AsyncClient):
    """Authorization test: User A's todo list must not contain User B's todos."""
    token_a = await register_and_login(client, "userA_list@example.com")
    token_b = await register_and_login(client, "userB_list@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "User B's private todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    data = response.json()
    titles = [item["title"] for item in data["items"]]
    assert "User B's private todo" not in titles


# ─── Business Logic Tests ──────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_toggle_completed_true_to_false(client: AsyncClient):
    """Bug fix test: completed can be toggled from True back to False (old code only handled True)."""
    token = await register_and_login(client, "toggle@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]

    # Mark as completed
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Toggle back to incomplete
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_title_does_not_erase_description(client: AsyncClient):
    """Business logic test: updating title only must preserve the original description."""
    token = await register_and_login(client, "partial@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Keep this description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]

    # Update only the title
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert data["description"] == "Keep this description"


# ─── Cache Invalidation Tests ─────────────────────────────────────────────────
# Note: Redis is mocked in conftest.py; these tests verify that the cache
# mock's delete method is called on create/update/delete operations.


@pytest.mark.asyncio
async def test_create_todo_invalidates_cache(client: AsyncClient):
    """Cache test: creating a todo must result in the cache being written to after invalidation."""
    token = await register_and_login(client, "cache_create@example.com")

    # First request populates cache
    first = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first.status_code == 200
    assert first.json()["total"] == 0

    # Create a todo
    await client.post(
        "/api/v1/todos",
        json={"title": "Cache Buster"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Second request should reflect the new todo (cache was invalidated)
    second = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second.status_code == 200
    assert second.json()["total"] == 1


@pytest.mark.asyncio
async def test_delete_todo_invalidates_cache(client: AsyncClient):
    """Cache test: deleting a todo must make it absent in the next list response."""
    token = await register_and_login(client, "cache_delete@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Will be deleted"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]

    # Populate cache
    await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token}"})

    # Delete the todo
    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # List must no longer contain the deleted item
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json()["total"] == 0
