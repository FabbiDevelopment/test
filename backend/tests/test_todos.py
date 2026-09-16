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
async def test_cross_user_todo_data_isolation(client: AsyncClient):
    """A user must not see or mutate another user's todos."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_user_token = await get_auth_token(client, "other-user@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_user_headers = {"Authorization": f"Bearer {other_user_token}"}

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Owner private todo", "description": "Private data"},
        headers=owner_headers,
    )
    assert create_response.status_code == 201
    owner_todo_id = create_response.json()["id"]

    list_response = await client.get(
        "/api/v1/todos",
        headers=other_user_headers,
    )
    assert list_response.status_code == 200
    assert owner_todo_id not in {
        todo["id"] for todo in list_response.json()["items"]
    }

    get_response = await client.get(
        f"/api/v1/todos/{owner_todo_id}",
        headers=other_user_headers,
    )
    assert get_response.status_code == 404
    assert get_response.json() == {"detail": "Todo not found"}

    update_response = await client.put(
        f"/api/v1/todos/{owner_todo_id}",
        json={"title": "Unauthorized update", "completed": True},
        headers=other_user_headers,
    )
    assert update_response.status_code == 404
    assert update_response.json() == {"detail": "Todo not found"}

    delete_response = await client.delete(
        f"/api/v1/todos/{owner_todo_id}",
        headers=other_user_headers,
    )
    assert delete_response.status_code == 404
    assert delete_response.json() == {"detail": "Todo not found"}

    owner_get_response = await client.get(
        f"/api/v1/todos/{owner_todo_id}",
        headers=owner_headers,
    )
    assert owner_get_response.status_code == 200
    owner_todo = owner_get_response.json()
    assert owner_todo["title"] == "Owner private todo"
    assert owner_todo["description"] == "Private data"
    assert owner_todo["completed"] is False
