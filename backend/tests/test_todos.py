"""Todo tests."""

import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone
from app.core.config import settings
from jose import jwt


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
async def test_expired_token_rejection(client: AsyncClient):
    """Test 1: Từ chối Token đã hết hạn hoặc bị sửa đổi trái phép (BUG-B01)."""
    # Tạo một JWT token có thời gian hết hạn trong quá khứ (-1 giờ)
    expired_payload = {
        "sub": "00000000-0000-0000-0000-000000000001",
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "type": "access",
    }
    expired_token = jwt.encode(
        expired_payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    # Gửi request với token hết hạn -> Backend bắt buộc phải từ chối (401)
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid authentication token"
    # Thử gửi token bị sửa đổi chữ ký (Tampered token)
    tampered_token = expired_token + "tampered_signature"
    response_tampered = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response_tampered.status_code == 401
@pytest.mark.asyncio
async def test_cross_user_authorization_boundary(client: AsyncClient):
    """Test 2: Kiểm tra ranh giới phân quyền IDOR - User A không thể xem, sửa, xóa Todo của User B (BUG-B02)."""
    # Tạo tài khoản User A và User B độc lập
    token_a = await get_auth_token(client, "user_a@example.com")
    token_b = await get_auth_token(client, "user_b@example.com")
    # User B tạo 1 Todo riêng tư
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Private Todo of User B", "description": "Confidential"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert create_res.status_code == 201
    todo_b_id = create_res.json()["id"]
    # 1. User A cố tình đọc trộm Todo của B -> Phải bị chặn 403 Forbidden!
    get_res = await client.get(
        f"/api/v1/todos/{todo_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert get_res.status_code == 403
    assert "Not authorized" in get_res.json()["detail"]
    # 2. User A cố tình sửa Todo của B -> Phải bị chặn 403!
    update_res = await client.put(
        f"/api/v1/todos/{todo_b_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert update_res.status_code == 403
    # 3. User A cố tình xóa Todo của B -> Phải bị chặn 403!
    delete_res = await client.delete(
        f"/api/v1/todos/{todo_b_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert delete_res.status_code == 403
@pytest.mark.asyncio
async def test_boolean_toggle_completed_to_false(client: AsyncClient):
    """Test 3: Kiểm tra chuyển đổi trạng thái completed từ True về False (BUG-B05)."""
    token = await get_auth_token(client, "toggle@example.com")
    # Tạo Todo ban đầu
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Test Item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    # Đổi completed sang True
    res_true = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_true.status_code == 200
    assert res_true.json()["completed"] is True
    # Bỏ tích hoàn thành (đổi về False) -> Backend bắt buộc phải lưu đúng False
    res_false = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_false.status_code == 200
    assert res_false.json()["completed"] is False
    # Gọi GET kiểm tra lại dữ liệu thực tế từ Database
    verify_res = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert verify_res.json()["completed"] is False
@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    """Test 4: Cập nhật từng phần (Partial Update) - Sửa Title không làm mất Description."""
    token = await get_auth_token(client, "partial@example.com")
    # Tạo Todo có đầy đủ Title và Description
    create_res = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Original Description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_res.json()["id"]
    # Chỉ sửa Title (không truyền trường description)
    update_res = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_res.status_code == 200
    data = update_res.json()
    assert data["title"] == "New Title Only"
    assert data["description"] == "Original Description"