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
async def test_authorization_boundary_cross_user(client: AsyncClient):
    """Test that User A cannot read, update, or delete User B's todos."""
    token_b = await get_auth_token(client, "user_b@example.com")
    token_a = await get_auth_token(client, "user_a@example.com")

    # User B creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo", "description": "Private to B"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]

    # 1. User A tries to GET User B's todo -> 403
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_res.status_code == 403

    # 2. User A tries to UPDATE User B's todo -> 403
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert update_res.status_code == 403

    # 3. User A tries to DELETE User B's todo -> 403
    delete_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert delete_res.status_code == 403

    # Verify todo still intact for User B
    b_get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert b_get_res.status_code == 200
    assert b_get_res.json()["title"] == "User B Todo"


@pytest.mark.asyncio
async def test_boolean_toggle_completed_persists(client: AsyncClient):
    """Test that updating completed from true back to false persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create todo (default completed = False)
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
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

    # Query GET to ensure DB persisted False
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_res.status_code == 200
    assert get_res.json()["completed"] is False


@pytest.mark.asyncio
async def test_cache_invalidation_on_mutation(client: AsyncClient, mock_redis):
    """Test that creating, updating, or deleting a todo invalidates stale Redis cache."""
    token = await get_auth_token(client, "cache_invalidation@example.com")

    # 1. Create a todo -> triggers cache delete
    mock_redis.delete.reset_mock()
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Invalidate Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_res.status_code == 201
    todo_id = create_res.json()["id"]
    assert mock_redis.delete.called

    # 2. Update todo -> triggers cache delete
    mock_redis.delete.reset_mock()
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    assert mock_redis.delete.called

    # 3. Delete todo -> triggers cache delete
    mock_redis.delete.reset_mock()
    del_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_res.status_code == 204
    assert mock_redis.delete.called
