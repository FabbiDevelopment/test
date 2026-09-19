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
async def test_cannot_get_other_users_todo(client: AsyncClient):
    """User B không thể GET todo của User A — trả về 404."""
    token_a = await get_auth_token(client, "idor-a@example.com")
    token_b = await get_auth_token(client, "idor-b@example.com")

    # User A tạo 1 todo
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "A's secret todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố GET todo của A
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_cannot_update_other_users_todo(client: AsyncClient):
    """User B không thể PUT todo của User A — trả về 404, title không bị đổi."""
    token_a = await get_auth_token(client, "idor-update-a@example.com")
    token_b = await get_auth_token(client, "idor-update-b@example.com")

    original_title = "A's original title"
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": original_title},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố PUT todo của A
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404

    # Xác nhận title của A vẫn không đổi
    verify_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["title"] == original_title


@pytest.mark.asyncio
async def test_cannot_delete_other_users_todo(client: AsyncClient):
    """User B không thể DELETE todo của User A — trả về 404, todo vẫn còn tồn tại."""
    token_a = await get_auth_token(client, "idor-delete-a@example.com")
    token_b = await get_auth_token(client, "idor-delete-b@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Don't delete me"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = create_resp.json()["id"]

    # User B cố DELETE todo của A
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 404

    # Xác nhận todo của A vẫn còn tồn tại
    verify_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert verify_resp.status_code == 200


@pytest.mark.asyncio
async def test_cache_isolated_between_users(client: AsyncClient):
    """Cache của user A không được trả về cho user B."""
    token_a = await get_auth_token(client, "cache-a@example.com")
    token_b = await get_auth_token(client, "cache-b@example.com")

    # User A tạo 1 todo
    await client.post(
        "/api/v1/todos",
        json={"title": "A's todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    # User A gọi GET /todos để populate cache của A
    resp_a = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert resp_a.status_code == 200
    assert resp_a.json()["total"] == 1

    # User B gọi GET /todos — không được thấy todo của A
    resp_b = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert resp_b.status_code == 200
    data_b = resp_b.json()
    assert data_b["total"] == 0
    assert len(data_b["items"]) == 0


@pytest.mark.asyncio
async def test_cache_invalidated_after_create(client: AsyncClient):
    """Cache phải bị invalidate sau khi tạo todo mới."""
    token = await get_auth_token(client, "cache-inv@example.com")

    # Tạo todo đầu tiên
    await client.post(
        "/api/v1/todos",
        json={"title": "First Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # GET lần 1 — populate cache, assert total == 1
    resp1 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp1.status_code == 200
    assert resp1.json()["total"] == 1

    # Tạo todo thứ hai (phải invalidate cache)
    await client.post(
        "/api/v1/todos",
        json={"title": "Second Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # GET lần 2 — vẫn trong TTL, nhưng cache đã bị invalidate → phải thấy total == 2
    resp2 = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp2.status_code == 200
    assert resp2.json()["total"] == 2


@pytest.mark.asyncio
async def test_toggle_completed_false_persists(client: AsyncClient):
    """Bug 5 fix: PUT {"completed": false} phải thực sự lưu False vào DB."""
    token = await get_auth_token(client, "bug5@example.com")

    # Tạo todo (mặc định completed=False)
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Test"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    todo_id = create_resp.json()["id"]

    # PUT {"completed": true} → phải thành True
    resp_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_true.status_code == 200
    assert resp_true.json()["completed"] is True

    # PUT {"completed": false} → phải thành False (assertion quan trọng nhất)
    resp_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp_false.status_code == 200
    assert resp_false.json()["completed"] is False

    # GET lại để xác nhận DB đã lưu đúng (không chỉ đúng ở response PUT)
    get_resp = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Bug 6 fix: PUT chỉ gửi title không được ghi đè description thành None."""
    token = await get_auth_token(client, "bug6@example.com")

    # Tạo todo với title và description
    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Important notes"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_resp.status_code == 201
    todo_id = create_resp.json()["id"]

    # PUT CHỈ với title (không gửi description trong body)
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New Title"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    # description KHÔNG được bị mất (assertion quan trọng nhất)
    assert data["description"] == "Important notes"
