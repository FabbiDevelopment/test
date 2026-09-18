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
async def test_user_cannot_access_another_users_todo(client: AsyncClient):
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private todo"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    todo_id = create_response.json()["id"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    get_response = await client.get(f"/api/v1/todos/{todo_id}", headers=other_headers)
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen"},
        headers=other_headers,
    )
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}", headers=other_headers
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


@pytest.mark.asyncio
async def test_completed_can_be_changed_from_true_to_false(client: AsyncClient):
    token = await get_auth_token(client, "toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post(
        "/api/v1/todos", json={"title": "Toggle me"}, headers=headers
    )
    todo_id = create_response.json()["id"]

    await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    response = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": False}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_title_update_preserves_description(client: AsyncClient):
    token = await get_auth_token(client, "partial@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Old title", "description": "Keep this"},
        headers=headers,
    )
    todo_id = create_response.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New title"},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["title"] == "New title"
    assert response.json()["description"] == "Keep this"


@pytest.mark.asyncio
async def test_todo_cache_is_scoped_and_invalidated(
    client: AsyncClient, redis_mock
):
    token = await get_auth_token(client, "cache@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    me_response = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me_response.json()["id"]
    await client.get("/api/v1/todos?page=2&size=10", headers=headers)
    redis_mock.set.assert_awaited_once()
    cache_key = redis_mock.set.await_args.args[0]
    assert cache_key == f"todos:list:{user_id}:2:10"

    redis_mock.delete_pattern.reset_mock()
    create_response = await client.post(
        "/api/v1/todos", json={"title": "Cache invalidation"}, headers=headers
    )
    todo_id = create_response.json()["id"]
    await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)

    expected_pattern = f"todos:list:{user_id}:*"
    assert redis_mock.delete_pattern.await_count == 3
    for call in redis_mock.delete_pattern.await_args_list:
        assert call.args == (expected_pattern,)
