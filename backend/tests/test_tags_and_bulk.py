"""Pytest suite for Tier 4: Todo Tags, Filtering, and Bulk Actions."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str) -> str:
    """Helper function to register and return access token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password@123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success_and_case_insensitivity(client: AsyncClient):
    """Test creating tag and preventing duplicate casing."""
    token = await get_auth_token(client, "tag_user@example.com")

    # 1. Create tag "Work"
    res1 = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#ff0000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res1.status_code == 201
    assert res1.json()["name"] == "Work"

    # 2. Try creating duplicate "work" (case-insensitive) -> 400
    res2 = await client.post(
        "/api/v1/tags",
        json={"name": "work", "color": "#00ff00"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_cross_user_tag_attaching_prevention(client: AsyncClient):
    """Test that User B cannot attach User A's tag or access User A's tags."""
    token_a = await get_auth_token(client, "tag_usera@example.com")
    token_b = await get_auth_token(client, "tag_userb@example.com")

    # User A creates tag
    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "User A Tag"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    tag_id_a = tag_res.json()["id"]

    # User B creates a todo
    todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "User B Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_id_b = todo_res.json()["id"]

    # User B tries to attach User A's tag -> 404
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id_b}/tags/{tag_id_a}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert attach_res.status_code == 404


@pytest.mark.asyncio
async def test_filter_todos_by_tag_and_status(client: AsyncClient):
    """Test filtering todos by tag and completion status."""
    token = await get_auth_token(client, "filter_user@example.com")

    # Create tag
    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "Urgent"},
        headers={"Authorization": f"Bearer {token}"},
    )
    tag_id = tag_res.json()["id"]

    # Create 2 todos
    todo1_res = await client.post(
        "/api/v1/todos",
        json={"title": "Tagged Completed Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo1_id = todo1_res.json()["id"]

    await client.post(
        "/api/v1/todos",
        json={"title": "Untagged Active Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Attach tag to todo1
    await client.post(
        f"/api/v1/todos/{todo1_id}/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    # Mark todo1 completed
    await client.put(
        f"/api/v1/todos/{todo1_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Filter by status=completed & tag_id
    filter_res = await client.get(
        f"/api/v1/todos?status=completed&tag_id={tag_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert filter_res.status_code == 200
    data = filter_res.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["id"] == todo1_id


@pytest.mark.asyncio
async def test_bulk_status_update(client: AsyncClient):
    """Test bulk status update in transaction and ownership checks."""
    token_a = await get_auth_token(client, "bulk_usera@example.com")
    token_b = await get_auth_token(client, "bulk_userb@example.com")

    # User A creates 2 todos
    t1 = (await client.post("/api/v1/todos", json={"title": "T1"}, headers={"Authorization": f"Bearer {token_a}"})).json()["id"]
    t2 = (await client.post("/api/v1/todos", json={"title": "T2"}, headers={"Authorization": f"Bearer {token_a}"})).json()["id"]

    # User B creates 1 todo
    tb = (await client.post("/api/v1/todos", json={"title": "TB"}, headers={"Authorization": f"Bearer {token_b}"})).json()["id"]

    # 1. User A bulk updates t1 & t2 -> 200
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1, t2], "completed": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2

    # Verify both are completed
    res1 = await client.get(f"/api/v1/todos/{t1}", headers={"Authorization": f"Bearer {token_a}"})
    assert res1.json()["completed"] is True

    # 2. User A tries to include User B's todo `tb` in bulk update -> 403
    forbidden_bulk = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1, tb], "completed": False},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert forbidden_bulk.status_code == 403
