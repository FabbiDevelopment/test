"""Todo tests."""

import pytest
from httpx import AsyncClient

from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from app.models.todo import Todo
from app.models.user import User

@pytest.mark.asyncio
async def test_toggle_completed_back_to_false(client: AsyncClient):
    token = await get_auth_token(client, "toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle me"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    completed = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers=headers,
    )
    assert completed.status_code == 200
    assert completed.json()["completed"] is True

    reopened = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers=headers,
    )
    assert reopened.status_code == 200
    assert reopened.json()["completed"] is False

    saved = await client.get(
    f"/api/v1/todos/{todo_id}",
    headers=headers,
)

    assert saved.status_code == 200
    assert saved.json()["completed"] is False

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
async def test_list_todos_orders_newest_first(
    client: AsyncClient,
    db_session,
):
    email = "ordered@example.com"
    token = await get_auth_token(client, email)
    headers = {"Authorization": f"Bearer {token}"}

    result = await db_session.execute(
        select(User).where(User.email == email)
    )
    user = result.scalar_one()

    now = datetime.now(timezone.utc)
    db_session.add_all(
        [
            Todo(
                title="Older todo",
                user_id=user.id,
                created_at=now - timedelta(minutes=2),
                updated_at=now - timedelta(minutes=2),
            ),
            Todo(
                title="Newer todo",
                user_id=user.id,
                created_at=now - timedelta(minutes=1),
                updated_at=now - timedelta(minutes=1),
            ),
        ]
    )
    await db_session.commit()

    response = await client.get("/api/v1/todos", headers=headers)

    assert response.status_code == 200
    titles = [todo["title"] for todo in response.json()["items"]]
    assert titles == ["Newer todo", "Older todo"]

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
async def test_title_update_preserves_description(client: AsyncClient):
    token = await get_auth_token(client, "partial@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos",
        json={
            "title": "Original title",
            "description": "Keep this description",
        },
        headers=headers,
    )
    todo_id = created.json()["id"]

    updated = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Renamed title"},
        headers=headers,
    )

    assert updated.status_code == 200

    saved = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
    )

    assert saved.json()["title"] == "Renamed title"
    assert saved.json()["description"] == "Keep this description"

@pytest.mark.asyncio
async def test_user_cannot_access_another_users_todo(client: AsyncClient):
    token_b = await get_auth_token(client, "user-b@example.com")
    headers_b = {"Authorization": f"Bearer {token_b}"}

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Private todo"},
        headers=headers_b,
    )
    todo_id = created.json()["id"]

    token_a = await get_auth_token(client, "user-a@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    read_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers_a,
    )
    assert read_response.status_code == 404

    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hijacked todo"},
        headers=headers_a,
    )
    assert update_response.status_code == 404

    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers=headers_a,
    )
    assert delete_response.status_code == 404

    owner_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers_b,
    )
    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == "Private todo"