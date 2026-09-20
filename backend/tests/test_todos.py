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
async def test_authorization_boundary_cross_user_isolation(client: AsyncClient):
    """Test that User A cannot read, update, or delete User B's todos."""
    user_a_token = await get_auth_token(client, "user_a@example.com")
    user_b_token = await get_auth_token(client, "user_b@example.com")

    # User A creates a todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "User A Private Todo", "description": "Confidential"},
        headers={"Authorization": f"Bearer {user_a_token}"},
    )
    assert create_resp.status_code == 201
    todo_a_id = create_resp.json()["id"]

    # User B cannot read User A's todo by ID
    get_resp = await client.get(
        f"/api/v1/todos/{todo_a_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert get_resp.status_code == 404

    # User B cannot update User A's todo
    put_resp = await client.put(
        f"/api/v1/todos/{todo_a_id}",
        json={"title": "Hacked by B"},
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert put_resp.status_code == 404

    # User B cannot delete User A's todo
    del_resp = await client.delete(
        f"/api/v1/todos/{todo_a_id}",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert del_resp.status_code == 404

    # User B's list does not contain User A's todo
    list_resp = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {user_b_token}"},
    )
    assert list_resp.status_code == 200
    b_todo_ids = [item["id"] for item in list_resp.json()["items"]]
    assert todo_a_id not in b_todo_ids


@pytest.mark.asyncio
async def test_boolean_toggle_completed_true_to_false(client: AsyncClient):
    """Test that updating completed status from true back to false persists correctly."""
    token = await get_auth_token(client, "toggle@example.com")

    # Create todo (default completed=False)
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]
    assert create_resp.json()["completed"] is False

    # Toggle to True
    toggle_true_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert toggle_true_resp.status_code == 200
    assert toggle_true_resp.json()["completed"] is True

    # Toggle back to False
    toggle_false_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert toggle_false_resp.status_code == 200
    assert toggle_false_resp.json()["completed"] is False

    # Verify persistence via GET
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test that updating only the title does not erase an existing description."""
    token = await get_auth_token(client, "partial@example.com")

    # Create todo with description
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Important Details"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_resp.json()["id"]
    assert create_resp.json()["description"] == "Important Details"

    # Partial update: title only
    update_resp = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["title"] == "Updated Title Only"
    assert data["description"] == "Important Details"


@pytest.mark.asyncio
async def test_deterministic_ordering_todos(client: AsyncClient):
    """Test that todos are consistently ordered by created_at desc, id desc."""
    token = await get_auth_token(client, "order@example.com")

    # Create multiple todos
    created_ids = []
    for i in range(3):
        resp = await client.post(
            "/api/v1/todos",
            json={"title": f"Item {i}"},
            headers={"Authorization": f"Bearer {token}"},
        )
        created_ids.append(resp.json()["id"])

    # Fetch todos
    list_resp = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_resp.status_code == 200
    returned_ids = [item["id"] for item in list_resp.json()["items"]]

    # Most recent should be first
    assert returned_ids[:3] == list(reversed(created_ids))


@pytest.mark.asyncio
async def test_bulk_delete_todos_success(client: AsyncClient):
    """Test bulk deleting multiple todos."""
    token = await get_auth_token(client, "bulk_del@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 todos
    t1 = (await client.post("/api/v1/todos", json={"title": "Item 1"}, headers=headers)).json()
    t2 = (await client.post("/api/v1/todos", json={"title": "Item 2"}, headers=headers)).json()
    t3 = (await client.post("/api/v1/todos", json={"title": "Item 3"}, headers=headers)).json()

    # Bulk delete t1 and t2
    del_resp = await client.post(
        "/api/v1/todos/bulk-delete",
        json={"todo_ids": [t1["id"], t2["id"]]},
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 2

    # Verify t1 and t2 are gone, t3 remains
    assert (await client.get(f"/api/v1/todos/{t1['id']}", headers=headers)).status_code == 404
    assert (await client.get(f"/api/v1/todos/{t2['id']}", headers=headers)).status_code == 404
    assert (await client.get(f"/api/v1/todos/{t3['id']}", headers=headers)).status_code == 200


@pytest.mark.asyncio
async def test_bulk_delete_todos_cross_user_isolation(client: AsyncClient):
    """Test User B cannot bulk delete User A's todos."""
    token_a = await get_auth_token(client, "del_a@example.com")
    token_b = await get_auth_token(client, "del_b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates 2 todos
    t1 = (await client.post("/api/v1/todos", json={"title": "A1"}, headers=headers_a)).json()
    t2 = (await client.post("/api/v1/todos", json={"title": "A2"}, headers=headers_a)).json()

    # User B attempts to bulk delete User A's todos
    del_resp = await client.post(
        "/api/v1/todos/bulk-delete",
        json={"todo_ids": [t1["id"], t2["id"]]},
        headers=headers_b,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 0

    # User A's todos still exist
    assert (await client.get(f"/api/v1/todos/{t1['id']}", headers=headers_a)).status_code == 200
    assert (await client.get(f"/api/v1/todos/{t2['id']}", headers=headers_a)).status_code == 200


@pytest.mark.asyncio
async def test_bulk_delete_todos_with_tags(client: AsyncClient):
    """Test bulk deleting todos with tags attached cleans up gracefully."""
    token = await get_auth_token(client, "bulk_tag_del@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create tag
    tag = (await client.post("/api/v1/tags", json={"name": "Work"}, headers=headers)).json()

    # Create todo and attach tag
    todo = (await client.post("/api/v1/todos", json={"title": "Tagged Todo"}, headers=headers)).json()
    await client.post(f"/api/v1/todos/{todo['id']}/tags", json={"tag_id": tag["id"]}, headers=headers)

    # Bulk delete todo
    del_resp = await client.post(
        "/api/v1/todos/bulk-delete",
        json={"todo_ids": [todo["id"]]},
        headers=headers,
    )
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_count"] == 1

    # Verify todo is deleted
    assert (await client.get(f"/api/v1/todos/{todo['id']}", headers=headers)).status_code == 404

    # Verify tag itself still exists
    tags_resp = await client.get("/api/v1/tags", headers=headers)
    assert tags_resp.status_code == 200
    assert any(t["id"] == tag["id"] for t in tags_resp.json()["items"])

