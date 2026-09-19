"""Todo endpoints tests."""

import pytest
from httpx import AsyncClient


async def create_authenticated_user(client: AsyncClient, email: str, password: str = "Password@123") -> tuple[str, str]:
    """Helper to register user and return (token, user_id)."""
    reg_response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert reg_response.status_code == 201
    token = reg_response.json()["access_token"]
    
    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    user_id = me_response.json()["id"]
    return token, user_id


@pytest.mark.asyncio
async def test_create_and_list_todos(client: AsyncClient):
    """Test creating a todo and listing todos for the user."""
    token, _ = await create_authenticated_user(client, "user1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Test Todo 1", "description": "Description 1"},
    )
    assert create_res.status_code == 201
    todo_data = create_res.json()
    assert todo_data["title"] == "Test Todo 1"
    assert todo_data["description"] == "Description 1"
    assert todo_data["completed"] is False

    list_res = await client.get("/api/v1/todos", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] == 1
    assert len(list_data["items"]) == 1
    assert list_data["items"][0]["id"] == todo_data["id"]


@pytest.mark.asyncio
async def test_authorization_boundary_cross_user_access(client: AsyncClient):
    """Test that User A cannot read, update, or delete User B's todos."""
    token_a, _ = await create_authenticated_user(client, "usera@example.com")
    token_b, _ = await create_authenticated_user(client, "userb@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a todo
    create_res = await client.post(
        "/api/v1/todos",
        headers=headers_a,
        json={"title": "Private Todo of A", "description": "Secret"},
    )
    assert create_res.status_code == 201
    todo_id = create_res.json()["id"]

    # User B tries to read User A's todo -> 404
    get_res = await client.get(f"/api/v1/todos/{todo_id}", headers=headers_b)
    assert get_res.status_code == 404

    # User B tries to update User A's todo -> 404
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        headers=headers_b,
        json={"title": "Hacked Title"},
    )
    assert update_res.status_code == 404

    # User B tries to delete User A's todo -> 404
    delete_res = await client.delete(f"/api/v1/todos/{todo_id}", headers=headers_b)
    assert delete_res.status_code == 404

    # User A's todo is intact
    check_res = await client.get(f"/api/v1/todos/{todo_id}", headers=headers_a)
    assert check_res.status_code == 200
    assert check_res.json()["title"] == "Private Todo of A"


@pytest.mark.asyncio
async def test_boolean_toggle_persists_correctly(client: AsyncClient):
    """Test that toggling completed from true back to false persists correctly."""
    token, _ = await create_authenticated_user(client, "toggle_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create todo (default completed=False)
    create_res = await client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Toggle Item", "description": "Testing toggle"},
    )
    todo_id = create_res.json()["id"]
    assert create_res.json()["completed"] is False

    # Update to completed=True
    update_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
        json={"completed": True},
    )
    assert update_true.status_code == 200
    assert update_true.json()["completed"] is True

    # Update to completed=False (toggle back)
    update_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
        json={"completed": False},
    )
    assert update_false.status_code == 200
    assert update_false.json()["completed"] is False

    # Verify persistence with GET
    get_res = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test that updating title does not erase description."""
    token, _ = await create_authenticated_user(client, "partial_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Initial Title", "description": "Important Details"},
    )
    todo_id = create_res.json()["id"]

    # Partial update: only update title
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
        json={"title": "New Title"},
    )
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "New Title"
    assert updated_data["description"] == "Important Details"


@pytest.mark.asyncio
async def test_delete_todo(client: AsyncClient):
    """Test deleting own todo."""
    token, _ = await create_authenticated_user(client, "del_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Delete Me"},
    )
    todo_id = create_res.json()["id"]

    del_res = await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)
    assert del_res.status_code == 204

    get_res = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
    assert get_res.status_code == 404
