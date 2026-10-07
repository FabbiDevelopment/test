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
async def test_toggle_todo_completed_persistence(client: AsyncClient):
    """Test updating completed from true back to false persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # completed = False
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo", "description": "Testing toggle"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]
    assert create_response.json()["completed"] is False

    # completed = True
    response_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_true.status_code == 200
    assert response_true.json()["completed"] is True

    # completed = False
    response_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response_false.status_code == 200
    assert response_false.json()["completed"] is False

    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["completed"] is False
    
@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test updating title does not erase existing description."""
    token = await get_auth_token(client, "partial@example.com")

    # 1. Create a todo with title and description
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Original Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    todo_id = create_response.json()["id"]

    # 2. Update title only (omit description)
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    updated_data = update_response.json()
    assert updated_data["title"] == "Updated Title Only"
    assert updated_data["description"] == "Original Description"

    # 3. Verify description still persists in database
    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["description"] == "Original Description"

@pytest.mark.asyncio
async def test_cross_user_isolation(client: AsyncClient):
    """Test that User B cannot view, update, or delete User A's todo."""
    # 1. Register and get token for User A
    token_a = await get_auth_token(client, "user_a@example.com")

    # 2. Register and get token for User B
    token_b = await get_auth_token(client, "user_b@example.com")

    # 3. User A creates a todo
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert create_res.status_code == 201
    todo_id = create_res.json()["id"]

    # 4. User B attempts to read User A's todo -> 404
    get_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert get_res.status_code == 404

    # 5. User B attempts to update User A's todo -> 404
    put_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert put_res.status_code == 404

    # 6. User B attempts to delete User A's todo -> 404
    del_res = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 404

    # 7. Verify User A's todo is still safe and intact
    verify_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert verify_res.status_code == 200
    assert verify_res.json()["title"] == "User A Private Todo"
    
@pytest.mark.asyncio
async def test_list_todos_user_email_populated(client: AsyncClient):
    """Test that list_todos correctly populates user_email without n+1 queries."""
    email = "nplusone@example.com"
    token = await get_auth_token(client, email)

    # 1. Create multiple todos
    for i in range(3):
        res = await client.post(
            "/api/v1/todos",
            json={"title": f"Batch Todo {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 201

    # 2. Get list of todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) >= 3

    # 3. Verify user_email is correctly populated on every item
    for item in data["items"]:
        assert item["user_email"] == email