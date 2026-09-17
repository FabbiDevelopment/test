"""Todo tests."""

import pytest
from httpx import AsyncClient

from tests.conftest import test_redis


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
async def test_update_todo_preserves_description_and_can_uncomplete(client: AsyncClient):
    token = await get_auth_token(client, "partial-update@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update me", "description": "Keep this"},
        headers=headers,
    )
    todo_id = create_response.json()["id"]

    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers=headers,
    )
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated", "completed": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Keep this"
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_user_cannot_access_another_users_todo(client: AsyncClient):
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private"},
        headers=owner_headers,
    )
    todo_id = create_response.json()["id"]

    assert (await client.get(f"/api/v1/todos/{todo_id}", headers=other_headers)).status_code == 404
    assert (await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen"},
        headers=other_headers,
    )).status_code == 404
    assert (await client.delete(
        f"/api/v1/todos/{todo_id}", headers=other_headers
    )).status_code == 404


@pytest.mark.asyncio
async def test_todo_mutations_invalidate_user_cache(client: AsyncClient):
    token = await get_auth_token(client, "cache@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Cache me"},
        headers=headers,
    )
    todo_id = create_response.json()["id"]
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Cached update"},
        headers=headers,
    )
    await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)

    assert test_redis.delete_pattern.await_count == 3


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
