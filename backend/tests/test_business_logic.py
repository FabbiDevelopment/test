"""
Business logic tests — Kiểm thử logic nghiệp vụ Todo.
Covers: completed toggle (true→false) and partial update integrity.
"""

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_get_token


@pytest.mark.asyncio
async def test_completed_toggle_true_to_false(client: AsyncClient):
    """
    THÊM: Kiểm tra công tắc Boolean completed — true → false phải được lưu chính xác.
    SAI (bug cũ): `if todo_data.completed:` bỏ qua giá trị False, không thể bỏ tick.
    """
    token = await register_and_get_token(client, "toggle@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle Todo", "description": "Test toggle"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Step 1: đánh dấu completed = true
    complete_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert complete_response.status_code == 200
    assert complete_response.json()["completed"] is True

    # Step 2: bỏ completed — true → false (regression test cho bug cũ)
    uncomplete_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert uncomplete_response.status_code == 200
    assert uncomplete_response.json()["completed"] is False

    # Step 3: xác minh persisted sau re-fetch
    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert get_response.status_code == 200
    assert get_response.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_title_preserves_description(client: AsyncClient):
    """
    THÊM: Partial update — chỉ sửa title không được xóa description.
    SAI (bug cũ): model_dump() không exclude_unset → description bị ghi None.
    """
    token = await register_and_get_token(client, "partial@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Original Title", "description": "Keep this description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title Only"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["title"] == "Updated Title Only"
    assert data["description"] == "Keep this description"
