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


@pytest.mark.asyncio
async def test_authorization_boundary_cross_user_isolation(client: AsyncClient):
    """Test that User A cannot read, update, or delete User B's todos."""
    token_a = await get_auth_token(client, "user_a_auth@example.com")
    token_b = await get_auth_token(client, "user_b_auth@example.com")

    # User A creates a todo
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo", "description": "Top Secret"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_res.status_code == 201
    todo_id = create_res.json()["id"]

    # User B tries to read User A's todo -> 403 Forbidden
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 403

    # User B tries to update User A's todo -> 403 Forbidden
    put_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_res.status_code == 403

    # User B tries to delete User A's todo -> 403 Forbidden
    del_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 403


@pytest.mark.asyncio
async def test_boolean_toggle_persistence(client: AsyncClient):
    """Test updating completed from true back to false persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create initial todo (completed = False)
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    assert create_res.json()["completed"] is False

    # Toggle to True
    res_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_true.status_code == 200
    assert res_true.json()["completed"] is True

    # Toggle back to False
    res_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_false.status_code == 200
    assert res_false.json()["completed"] is False

    # Verify persistence by fetching
    verify_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_res.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test updating title does not erase existing description."""
    token = await get_auth_token(client, "partial@example.com")

    # Create todo with description
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Initial Title", "description": "Important Details"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    # Partial update: change only title
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "Updated Title Only"
    assert data["description"] == "Important Details"


@pytest.mark.asyncio
async def test_cache_invalidation_lifecycle(client: AsyncClient):
    """Test creating, updating, or deleting a todo removes stale Redis cache."""
    token = await get_auth_token(client, "cachelifecycle@example.com")

    # 1. First fetch to seed empty cache
    res1 = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token}"})
    assert res1.json()["total"] == 0

    # 2. Create todo -> cache should be invalidated
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Fresh Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]

    # Next fetch must show total == 1
    res2 = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token}"})
    assert res2.json()["total"] == 1
    assert res2.json()["items"][0]["title"] == "Fresh Todo"

    # 3. Update todo -> cache should be invalidated
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Renamed Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Next fetch must reflect new title
    res3 = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token}"})
    assert res3.json()["items"][0]["title"] == "Renamed Todo"

    # 4. Delete todo -> cache should be invalidated
    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Next fetch must show total == 0
    res4 = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token}"})
    assert res4.json()["total"] == 0


@pytest.mark.asyncio
async def test_cache_user_isolation(client: AsyncClient):
    """Test that User B does not receive User A's cached todos."""
    token_a = await get_auth_token(client, "cache_a@example.com")
    token_b = await get_auth_token(client, "cache_b@example.com")

    # User A creates a todo and calls list -> cached
    await client.post(
        "/api/v1/todos",
        json={"title": "User A Unique Secret Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    res_a = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token_a}"})
    assert len(res_a.json()["items"]) == 1

    # User B calls list -> must NOT see User A's todo
    res_b = await client.get("/api/v1/todos", headers={"Authorization": f"Bearer {token_b}"})
    assert len(res_b.json()["items"]) == 0
