"""Todo tests."""

import pytest
from httpx import AsyncClient
from app.core.security import get_password_hash
from app.models.user import User


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
async def test_user_cannot_access_another_users_todo(
    client: AsyncClient,
    user,
    auth_headers_for,
    db_session,
):
    # User A creates a todo
    user_a_headers = auth_headers_for(user)

    create_response = await client.post(
        "/api/v1/todos",
        json={
            "title": "Private Todo",
            "description": "User A's private todo",
        },
        headers=user_a_headers,
    )

    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]

    # Create User B
    user_b = User(
        email="user-b@example.com",
        hashed_password=get_password_hash("password123"),
    )
    db_session.add(user_b)
    await db_session.commit()
    await db_session.refresh(user_b)

    user_b_headers = auth_headers_for(user_b)

    # User B cannot read User A's todo
    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=user_b_headers,
    )
    assert get_response.status_code == 404

    # User B cannot update User A's todo
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Todo"},
        headers=user_b_headers,
    )
    assert update_response.status_code == 404

    # User B cannot delete User A's todo
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers=user_b_headers,
    )
    assert delete_response.status_code == 404
    
    
@pytest.mark.asyncio
async def test_toggle_todo_true_to_false(
    client: AsyncClient,
    user,
    auth_headers_for,
):
    headers = auth_headers_for(user)

    # Create todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers=headers,
    )

    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]
    assert create_response.json()["completed"] is False

    # false -> true
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["completed"] is True

    # true -> false
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False

    # Verify persistence
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False
    
    
@pytest.mark.asyncio
async def test_partial_update_title_keeps_description(
    client: AsyncClient,
    user,
    auth_headers_for,
):
    headers = auth_headers_for(user)

    # Create todo with title and description
    create_response = await client.post(
        "/api/v1/todos",
        json={
            "title": "Original Title",
            "description": "Keep this description",
        },
        headers=headers,
    )

    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]

    # Update only title
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title"},
        headers=headers,
    )

    assert update_response.status_code == 200
    data = update_response.json()

    assert data["title"] == "Updated Title"
    assert data["description"] == "Keep this description"
    
    
@pytest.mark.asyncio
async def test_cache_invalidated_after_todo_mutations(
    client: AsyncClient,
    user,
    auth_headers_for,
    redis_mock,
):
    headers = auth_headers_for(user)
    expected_pattern = f"todos:list:{user.id}:*"

    # Create
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Todo"},
        headers=headers,
    )

    assert create_response.status_code == 201
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)

    todo_id = create_response.json()["id"]

    # Update
    redis_mock.delete_pattern.reset_mock()

    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Cache Todo"},
        headers=headers,
    )

    assert update_response.status_code == 200
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)

    # Delete
    redis_mock.delete_pattern.reset_mock()

    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
    )

    assert delete_response.status_code == 204
    redis_mock.delete_pattern.assert_awaited_once_with(expected_pattern)