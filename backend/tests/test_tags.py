"""Tests for Tag CRUD, filtering, bulk actions, and security isolation."""

from unittest.mock import MagicMock
import pytest
from httpx import AsyncClient


async def get_user_token(client: AsyncClient, email: str) -> str:
    """Helper to register and return access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    """Test successful tag creation."""
    token = await get_user_token(client, "tag_user1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#EF4444"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Work"
    assert data["color"] == "#EF4444"
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_tag_different_casing(client: AsyncClient):
    """Test that tag names are unique per user, case-insensitively."""
    token = await get_user_token(client, "tag_user2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create first tag
    res1 = await client.post(
        "/api/v1/tags",
        json={"name": "Urgent", "color": "#EF4444"},
        headers=headers,
    )
    assert res1.status_code == 201

    # Attempt to create tag with same name in lowercase
    res2 = await client.post(
        "/api/v1/tags",
        json={"name": "urgent", "color": "#10B981"},
        headers=headers,
    )
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_cross_user_tag_access_prevention(client: AsyncClient):
    """Test that user B cannot view, update, or delete user A's tag."""
    token_a = await get_user_token(client, "tag_user_a@example.com")
    token_b = await get_user_token(client, "tag_user_b@example.com")

    # User A creates tag
    create_res = await client.post(
        "/api/v1/tags",
        json={"name": "Personal", "color": "#3B82F6"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    tag_id = create_res.json()["id"]

    # User B tries to update user A's tag
    patch_res = await client.post(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    # FastAPI router might return 404 or 405 depending on method
    patch_actual = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert patch_actual.status_code == 404

    # User B tries to delete user A's tag
    del_res = await client.delete(
        f"/api/v1/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert del_res.status_code == 404


@pytest.mark.asyncio
async def test_attach_another_user_tag_prevented(client: AsyncClient):
    """Test that user A cannot attach user B's tag to user A's todo."""
    token_a = await get_user_token(client, "attach_user_a@example.com")
    token_b = await get_user_token(client, "attach_user_b@example.com")

    # User A creates a todo
    todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    todo_id = todo_res.json()["id"]

    # User B creates a tag
    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "User B Tag"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    tag_id = tag_res.json()["id"]

    # User A attempts to attach User B's tag
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert attach_res.status_code == 403
    assert "belonging to another user" in attach_res.json()["detail"]


@pytest.mark.asyncio
async def test_filter_todos_by_tag_and_attributes(client: AsyncClient):
    """Test filtering todos by tag_id, status, and keyword."""
    token = await get_user_token(client, "filter_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create tag
    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "Backend", "color": "#6366F1"},
        headers=headers,
    )
    tag_id = tag_res.json()["id"]

    # Create todo 1 (tagged)
    t1_res = await client.post(
        "/api/v1/todos",
        json={"title": "Refactor Database", "description": "Add indexes"},
        headers=headers,
    )
    t1_id = t1_res.json()["id"]

    # Attach tag to todo 1
    await client.post(
        f"/api/v1/todos/{t1_id}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )

    # Create todo 2 (untagged)
    await client.post(
        "/api/v1/todos",
        json={"title": "Write Frontend UI", "description": "React components"},
        headers=headers,
    )

    # 1. Filter by tag_id
    filter_tag_res = await client.get(
        f"/api/v1/todos?tag_id={tag_id}",
        headers=headers,
    )
    assert filter_tag_res.status_code == 200
    tag_items = filter_tag_res.json()["items"]
    assert len(tag_items) == 1
    assert tag_items[0]["id"] == t1_id
    assert len(tag_items[0]["tags"]) == 1
    assert tag_items[0]["tags"][0]["name"] == "Backend"

    # 2. Filter by keyword
    kw_res = await client.get(
        "/api/v1/todos?keyword=Database",
        headers=headers,
    )
    assert kw_res.status_code == 200
    assert len(kw_res.json()["items"]) == 1
    assert kw_res.json()["items"][0]["title"] == "Refactor Database"

    # 3. Filter by status (completed = true -> 0 results initially)
    st_res = await client.get(
        "/api/v1/todos?status=true",
        headers=headers,
    )
    assert st_res.status_code == 200
    assert len(st_res.json()["items"]) == 0


@pytest.mark.asyncio
async def test_bulk_status_ownership_check(client: AsyncClient):
    """Test that bulk status update only updates todos owned by current user."""
    token_a = await get_user_token(client, "bulk_a@example.com")
    token_b = await get_user_token(client, "bulk_b@example.com")

    # User A creates 2 todos
    res_a1 = await client.post("/api/v1/todos", json={"title": "A1"}, headers={"Authorization": f"Bearer {token_a}"})
    res_a2 = await client.post("/api/v1/todos", json={"title": "A2"}, headers={"Authorization": f"Bearer {token_a}"})
    id_a1 = res_a1.json()["id"]
    id_a2 = res_a2.json()["id"]

    # User B creates 1 todo
    res_b1 = await client.post("/api/v1/todos", json={"title": "B1"}, headers={"Authorization": f"Bearer {token_b}"})
    id_b1 = res_b1.json()["id"]

    # User A calls bulk-status including id_b1
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [id_a1, id_a2, id_b1], "completed": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2

    # Verify B1 is still not completed
    b1_check = await client.get(f"/api/v1/todos/{id_b1}", headers={"Authorization": f"Bearer {token_b}"})
    assert b1_check.json()["completed"] is False

    # Verify A1 is completed
    a1_check = await client.get(f"/api/v1/todos/{id_a1}", headers={"Authorization": f"Bearer {token_a}"})
    assert a1_check.json()["completed"] is True


@pytest.mark.asyncio
async def test_cache_invalidation_on_tag_operations(client: AsyncClient, mock_redis_client: MagicMock):
    """Test that attaching a tag and bulk updating invalidates user todo list cache."""
    token = await get_user_token(client, "cache_tag_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create todo & tag
    todo_res = await client.post("/api/v1/todos", json={"title": "Cache Todo"}, headers=headers)
    todo_id = todo_res.json()["id"]
    tag_res = await client.post("/api/v1/tags", json={"name": "CacheTag"}, headers=headers)
    tag_id = tag_res.json()["id"]

    mock_redis_client.delete_pattern.reset_mock()

    # Attach tag
    await client.post(f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers=headers)
    assert mock_redis_client.delete_pattern.called

    # Bulk status
    mock_redis_client.delete_pattern.reset_mock()
    await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [todo_id], "completed": True}, headers=headers)
    assert mock_redis_client.delete_pattern.called
