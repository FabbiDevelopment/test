import pytest
from httpx import AsyncClient

from tests.conftest import register_user


async def get_auth_token(client: AsyncClient, email: str = "tag_user@example.com") -> str:
    """Helper to register and get auth token."""
    response = await register_user(client, email=email)
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    """Test successful tag creation."""
    token = await get_auth_token(client, "tag_create@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#ef4444"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Work"
    assert data["color"] == "#ef4444"


@pytest.mark.asyncio
async def test_create_tag_duplicate_casing_fails(client: AsyncClient):
    """Test case-insensitive duplicate tag name prevention."""
    token = await get_auth_token(client, "tag_dup@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create 'Urgent'
    await client.post("/api/v1/tags", json={"name": "Urgent"}, headers=headers)

    # Attempt creating 'urgent' (lowercase)
    response = await client.post("/api/v1/tags", json={"name": "urgent"}, headers=headers)
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_attach_other_user_tag_forbidden(client: AsyncClient):
    """Test attaching another user's tag is forbidden."""
    token_a = await get_auth_token(client, "user_a_tag@example.com")
    token_b = await get_auth_token(client, "user_b_tag@example.com")

    # User A creates a tag
    res_tag = await client.post(
        "/api/v1/tags",
        json={"name": "PrivateTag"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    tag_a_id = res_tag.json()["id"]

    # User B creates a todo
    res_todo = await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_b_id = res_todo.json()["id"]

    # User B attempts to attach User A's tag
    response = await client.post(
        f"/api/v1/todos/{todo_b_id}/tags",
        json={"tag_id": tag_a_id},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_bulk_status_update_success_and_forbidden(client: AsyncClient):
    """Test bulk status update in a transaction and cross-user ownership enforcement."""
    token_a = await get_auth_token(client, "bulk_a@example.com")
    token_b = await get_auth_token(client, "bulk_b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}

    # User A creates 2 todos
    res1 = await client.post("/api/v1/todos", json={"title": "Todo A1"}, headers=headers_a)
    res2 = await client.post("/api/v1/todos", json={"title": "Todo A2"}, headers=headers_a)
    id1 = res1.json()["id"]
    id2 = res2.json()["id"]

    # Bulk update to completed = true
    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [id1, id2], "completed": True},
        headers=headers_a,
    )
    assert response.status_code == 200
    assert response.json()["updated_count"] == 2

    # User B creates a todo
    res_b = await client.post(
        "/api/v1/todos",
        json={"title": "Todo B"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    id_b = res_b.json()["id"]

    # User A attempts bulk update containing User B's todo ID
    bad_response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [id1, id_b], "completed": False},
        headers=headers_a,
    )
    assert bad_response.status_code == 403
