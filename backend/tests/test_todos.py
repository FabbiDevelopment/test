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
async def test_authorization_boundary_idor(client: AsyncClient):
    """Scenario 2: User A cannot read, update, or delete User B's todos."""
    user_a_token = await get_auth_token(client, "usera@example.com")
    user_b_token = await get_auth_token(client, "userb@example.com")

    # User A creates a private todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo", "description": "Secret notes"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert create_resp.status_code == 201
    todo_id = create_resp.json()["id"]

    # User B attempts to read User A's todo -> 403 Forbidden
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert get_resp.status_code == 403

    # User B attempts to update User A's todo -> 403 Forbidden
    put_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert put_resp.status_code == 403

    # User B attempts to delete User A's todo -> 403 Forbidden
    del_resp = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert del_resp.status_code == 403

    # Verify User A's todo still exists and is untouched
    verify_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["title"] == "User A Private Todo"


@pytest.mark.asyncio
async def test_boolean_toggle_completed_to_false(client: AsyncClient):
    """Scenario 3: Updating completed from true back to false persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]
    assert create_resp.json()["completed"] is False

    # Mark completed: True
    put_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_true.status_code == 200
    assert put_true.json()["completed"] is True

    # Mark completed: False (Boolean toggle back)
    put_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_false.status_code == 200
    assert put_false.json()["completed"] is False

    # Confirm persisted state via GET
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Scenario 4: Updating title does not erase existing description."""
    token = await get_auth_token(client, "partial@example.com")

    # Create with title and description
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Original Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]

    # Partial update: only update title
    put_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Modified Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_resp.status_code == 200
    updated_data = put_resp.json()
    assert updated_data["title"] == "Modified Title"
    assert updated_data["description"] == "Original Description"

    # Confirm persisted state via GET
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["description"] == "Original Description"


@pytest.mark.asyncio
async def test_cache_invalidation_on_mutations(client: AsyncClient, fake_redis):
    """Scenario 5: Creating, updating, or deleting a todo removes stale Redis cache."""
    token = await get_auth_token(client, "cache@example.com")

    # 1. Create todo triggers cache invalidation
    fake_redis.delete_pattern.reset_mock()
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Cache Test Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    todo_id = create_resp.json()["id"]
    assert fake_redis.delete_pattern.called

    # 2. Update todo triggers cache invalidation
    fake_redis.delete_pattern.reset_mock()
    put_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Cache Test Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert put_resp.status_code == 200
    assert fake_redis.delete_pattern.called

    # 3. Delete todo triggers cache invalidation
    fake_redis.delete_pattern.reset_mock()
    del_resp = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert del_resp.status_code == 204
    assert fake_redis.delete_pattern.called

