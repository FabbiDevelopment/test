"""Todo tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_redis
from app.main import app


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
async def test_user_cannot_read_update_or_delete_another_users_todo(
    client: AsyncClient,
):
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Owner only"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    todo_id = create_response.json()["id"]
    other_headers = {"Authorization": f"Bearer {other_token}"}

    read_response = await client.get(f"/api/v1/todos/{todo_id}", headers=other_headers)
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen"},
        headers=other_headers,
    )
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}", headers=other_headers
    )

    assert read_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


@pytest.mark.asyncio
async def test_partial_update_preserves_description_and_can_toggle_false(
    client: AsyncClient,
):
    token = await get_auth_token(client, "partial@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original", "description": "Keep this"},
        headers=headers,
    )
    todo_id = create_response.json()["id"]

    completed_response = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    active_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Renamed", "completed": False},
        headers=headers,
    )

    assert completed_response.json()["completed"] is True
    assert active_response.json()["completed"] is False
    assert active_response.json()["description"] == "Keep this"


@pytest.mark.asyncio
async def test_todo_mutations_invalidate_current_users_cache(client: AsyncClient):
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete_pattern = AsyncMock()
    previous_override = app.dependency_overrides[get_redis]
    app.dependency_overrides[get_redis] = lambda: redis

    try:
        token = await get_auth_token(client, "cache@example.com")
        headers = {"Authorization": f"Bearer {token}"}
        create_response = await client.post(
            "/api/v1/todos", json={"title": "Cached"}, headers=headers
        )
        todo = create_response.json()
        pattern = f"todos:{todo['user_id']}:*"

        await client.put(
            f"/api/v1/todos/{todo['id']}",
            json={"completed": True},
            headers=headers,
        )
        await client.delete(f"/api/v1/todos/{todo['id']}", headers=headers)

        assert redis.delete_pattern.await_count == 3
        redis.delete_pattern.assert_awaited_with(pattern)
    finally:
        app.dependency_overrides[get_redis] = previous_override
