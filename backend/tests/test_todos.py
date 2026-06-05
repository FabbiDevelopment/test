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
    """Test users cannot read, update, or delete another user's todo."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private Todo"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    todo_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert get_response.status_code == 404

    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen Todo"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert update_response.status_code == 404

    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    assert delete_response.status_code == 404

    owner_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == "Private Todo"


@pytest.mark.asyncio
async def test_todo_list_cache_is_isolated_by_user(client: AsyncClient):
    """Test cached todo lists are isolated between users."""
    first_token = await get_auth_token(client, "cache-user-a@example.com")
    second_token = await get_auth_token(client, "cache-user-b@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo"},
        headers={"Authorization": f"Bearer {first_token}"},
    )
    await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo"},
        headers={"Authorization": f"Bearer {second_token}"},
    )

    first_response = await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    assert first_response.status_code == 200
    assert first_response.json()["items"][0]["title"] == "User A Todo"

    second_response = await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {second_token}"},
    )
    assert second_response.status_code == 200
    assert second_response.json()["items"][0]["title"] == "User B Todo"


@pytest.mark.asyncio
async def test_todo_list_cache_is_isolated_by_page_and_size(client: AsyncClient):
    """Test cached todo lists are isolated by pagination parameters."""
    token = await get_auth_token(client, "cache-pagination@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "First Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.post(
        "/api/v1/todos",
        json={"title": "Second Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    first_page = await client.get(
        "/api/v1/todos?page=1&size=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first_page.status_code == 200
    assert first_page.json()["page"] == 1
    assert first_page.json()["size"] == 1
    assert len(first_page.json()["items"]) == 1

    second_page = await client.get(
        "/api/v1/todos?page=2&size=1",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second_page.status_code == 200
    assert second_page.json()["page"] == 2
    assert second_page.json()["size"] == 1
    assert len(second_page.json()["items"]) == 1


@pytest.mark.asyncio
async def test_todo_list_cache_invalidates_after_create(client: AsyncClient):
    """Test creating a todo invalidates cached lists for that user."""
    token = await get_auth_token(client, "cache-create@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "Existing Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    first_list = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert first_list.json()["total"] == 1

    await client.post(
        "/api/v1/todos",
        json={"title": "New Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    second_list = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert second_list.json()["total"] == 2


@pytest.mark.asyncio
async def test_todo_list_cache_invalidates_after_update(client: AsyncClient):
    """Test updating a todo invalidates cached lists for that user."""
    token = await get_auth_token(client, "cache-update@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Before Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "After Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json()["items"][0]["title"] == "After Update"


@pytest.mark.asyncio
async def test_todo_list_cache_invalidates_after_delete(client: AsyncClient):
    """Test deleting a todo invalidates cached lists for that user."""
    token = await get_auth_token(client, "cache-delete@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete From Cache"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    cached_list = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert cached_list.json()["total"] == 1

    await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_update_todo_can_set_completed_false(client: AsyncClient):
    """Test completed can be updated from true back to false."""
    token = await get_auth_token(client, "completed-false@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    true_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert true_response.status_code == 200
    assert true_response.json()["completed"] is True

    false_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert false_response.status_code == 200
    assert false_response.json()["completed"] is False
