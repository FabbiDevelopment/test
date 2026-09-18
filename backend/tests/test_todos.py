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
async def test_cross_user_isolation(client: AsyncClient):
    """Test that User B cannot access User A's todo."""
    token_a = await get_auth_token(client, "usera@example.com")
    token_b = await get_auth_token(client, "userb@example.com")

    # User A creates a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Secret of A"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_response.json()["id"]

    # User B tries to GET it
    response_get = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response_get.status_code in [403, 404]

    # User B tries to PUT it
    response_put = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response_put.status_code in [403, 404]
    
    # User B tries to DELETE it
    response_delete = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response_delete.status_code in [403, 404]


@pytest.mark.asyncio
async def test_boolean_toggle(client: AsyncClient):
    """Test updating completed from true back to false."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Complete it
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Uncomplete it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update(client: AsyncClient):
    """Test that updating title does not erase description."""
    token = await get_auth_token(client, "partial@example.com")

    # Create a todo with description
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Initial Title", "description": "Important Details"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update only the title
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Important Details"  # Should not be erased


@pytest.mark.asyncio
async def test_cache_invalidation(client: AsyncClient):
    """Test that creating a todo removes stale Redis cache."""
    from app.main import app
    from app.api.deps import get_redis
    from unittest.mock import AsyncMock, MagicMock
    
    token = await get_auth_token(client, "cache@example.com")
    
    # Create a specific mock for this test
    specific_mock = MagicMock()
    specific_mock.get = AsyncMock(return_value=None)
    specific_mock.set = AsyncMock()
    specific_mock.delete_by_pattern = AsyncMock()
    
    app.dependency_overrides[get_redis] = lambda: specific_mock
    
    # Create a todo
    response = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Invalidation Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    
    # Check that delete_by_pattern was called
    specific_mock.delete_by_pattern.assert_called()
    
    # Restore the original override
    from tests.conftest import override_get_redis
    app.dependency_overrides[get_redis] = override_get_redis
