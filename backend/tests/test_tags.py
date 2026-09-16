"""Tests for Tier 4: Tags, Advanced Filtering & Bulk Actions."""

import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "tag_user@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    """Test creating a new tag successfully."""
    token = await get_auth_token(client, "user_tag1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        "/api/v1/tags",
        json={"name": "Urgent", "color": "#ef4444"},
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Urgent"
    assert data["color"] == "#ef4444"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_tag_case_insensitive_duplicate_prevented(client: AsyncClient):
    """Test preventing duplicate tag names case-insensitively (e.g., 'Work' vs 'work')."""
    token = await get_auth_token(client, "user_tag_dup@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # First tag
    res1 = await client.post("/api/v1/tags", json={"name": "Work", "color": "#3b82f6"}, headers=headers)
    assert res1.status_code == 201

    # Duplicate tag with different casing
    res2 = await client.post("/api/v1/tags", json={"name": "work", "color": "#10b981"}, headers=headers)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_tag_idor_protection(client: AsyncClient):
    """Test IDOR protection: User B cannot get, update, or delete User A's tag."""
    token_a = await get_auth_token(client, "user_a@example.com")
    token_b = await get_auth_token(client, "user_b@example.com")

    # User A creates tag
    create_res = await client.post(
        "/api/v1/tags",
        json={"name": "Secret A", "color": "#123456"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    tag_id = create_res.json()["id"]

    # User B lists tags - should NOT see User A's tag
    list_res = await client.get("/api/v1/tags", headers={"Authorization": f"Bearer {token_b}"})
    assert list_res.status_code == 200
    tags_b = list_res.json()
    assert all(t["id"] != tag_id for t in tags_b)

    # User B tries to update User A's tag -> 404
    update_res = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert update_res.status_code == 404

    # User B tries to delete User A's tag -> 404
    delete_res = await client.delete(
        f"/api/v1/tags/{tag_id}",
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert delete_res.status_code == 404


@pytest.mark.asyncio
async def test_attach_and_detach_tag_to_todo(client: AsyncClient):
    """Test attaching and detaching tags to/from todos."""
    token = await get_auth_token(client, "user_attach@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create a tag
    tag_res = await client.post("/api/v1/tags", json={"name": "Backend", "color": "#6366f1"}, headers=headers)
    tag_id = tag_res.json()["id"]

    # 2. Create a todo
    todo_res = await client.post("/api/v1/todos", json={"title": "Fix API Bug"}, headers=headers)
    todo_id = todo_res.json()["id"]

    # 3. Attach tag
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )
    assert attach_res.status_code == 200
    todo_data = attach_res.json()
    assert len(todo_data["tags"]) == 1
    assert todo_data["tags"][0]["id"] == tag_id
    assert todo_data["tags"][0]["name"] == "Backend"

    # 4. Detach tag
    detach_res = await client.delete(
        f"/api/v1/todos/{todo_id}/tags/{tag_id}",
        headers=headers,
    )
    assert detach_res.status_code == 200
    updated_todo = detach_res.json()
    assert len(updated_todo["tags"]) == 0


@pytest.mark.asyncio
async def test_attach_tag_idor_prevention(client: AsyncClient):
    """Test that User B cannot attach User A's tag, nor attach to User A's todo."""
    token_a = await get_auth_token(client, "idor_a@example.com")
    token_b = await get_auth_token(client, "idor_b@example.com")

    # User A creates todo and tag
    todo_a = (await client.post("/api/v1/todos", json={"title": "Todo A"}, headers={"Authorization": f"Bearer {token_a}"})).json()
    tag_a = (await client.post("/api/v1/tags", json={"name": "Tag A"}, headers={"Authorization": f"Bearer {token_a}"})).json()

    # User B creates todo and tag
    todo_b = (await client.post("/api/v1/todos", json={"title": "Todo B"}, headers={"Authorization": f"Bearer {token_b}"})).json()
    tag_b = (await client.post("/api/v1/tags", json={"name": "Tag B"}, headers={"Authorization": f"Bearer {token_b}"})).json()

    # User B tries to attach Tag A to Todo B -> 404 (Tag not found or not owned)
    res1 = await client.post(
        f"/api/v1/todos/{todo_b['id']}/tags",
        json={"tag_id": tag_a["id"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res1.status_code == 404

    # User B tries to attach Tag B to Todo A -> 403 (Todo not owned)
    res2 = await client.post(
        f"/api/v1/todos/{todo_a['id']}/tags",
        json={"tag_id": tag_b["id"]},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert res2.status_code == 403


@pytest.mark.asyncio
async def test_advanced_filtering(client: AsyncClient):
    """Test filtering todos by status, keyword, and tag."""
    token = await get_auth_token(client, "filter_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create tag
    tag = (await client.post("/api/v1/tags", json={"name": "Priority"}, headers=headers)).json()

    # Create todos:
    # 1. Active with tag and keyword "Report"
    t1 = (await client.post("/api/v1/todos", json={"title": "Quarterly Report", "description": "Draft Q3"}, headers=headers)).json()
    await client.post(f"/api/v1/todos/{t1['id']}/tags", json={"tag_id": tag["id"]}, headers=headers)

    # 2. Completed with keyword "Report" but no tag
    t2 = (await client.post("/api/v1/todos", json={"title": "Annual Report", "description": "Review"}, headers=headers)).json()
    await client.put(f"/api/v1/todos/{t2['id']}", json={"completed": True}, headers=headers)

    # 3. Active with keyword "Meeting" and no tag
    await client.post("/api/v1/todos", json={"title": "Team Meeting", "description": "Discuss roadmap"}, headers=headers)

    # Filter 1: status=active -> should get t1 and t3 (2 items)
    r1 = await client.get("/api/v1/todos?status=active", headers=headers)
    assert r1.status_code == 200
    assert r1.json()["total"] == 2
    assert all(item["completed"] is False for item in r1.json()["items"])

    # Filter 2: keyword=Report -> should get t1 and t2 (2 items)
    r2 = await client.get("/api/v1/todos?keyword=Report", headers=headers)
    assert r2.status_code == 200
    assert r2.json()["total"] == 2

    # Filter 3: tag_id=Priority -> should get only t1 (1 item)
    r3 = await client.get(f"/api/v1/todos?tag_id={tag['id']}", headers=headers)
    assert r3.status_code == 200
    assert r3.json()["total"] == 1
    assert r3.json()["items"][0]["id"] == t1["id"]

    # Filter 4: combination status=active & keyword=Report & tag_id=Priority
    r4 = await client.get(f"/api/v1/todos?status=active&keyword=Report&tag_id={tag['id']}", headers=headers)
    assert r4.status_code == 200
    assert r4.json()["total"] == 1
    assert r4.json()["items"][0]["id"] == t1["id"]


@pytest.mark.asyncio
async def test_bulk_status_update_transaction_and_idor(client: AsyncClient):
    """Test bulk update of todos completed status and atomic IDOR protection."""
    token_a = await get_auth_token(client, "bulk_a@example.com")
    token_b = await get_auth_token(client, "bulk_b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates 2 active todos
    t1 = (await client.post("/api/v1/todos", json={"title": "Bulk 1"}, headers=headers_a)).json()
    t2 = (await client.post("/api/v1/todos", json={"title": "Bulk 2"}, headers=headers_a)).json()

    # User B creates 1 todo
    tb = (await client.post("/api/v1/todos", json={"title": "User B Todo"}, headers=headers_b)).json()

    # Bulk update for User A: mark t1 and t2 completed -> True
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1["id"], t2["id"]], "completed": True},
        headers=headers_a,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2

    # Verify both are now completed
    check_t1 = (await client.get(f"/api/v1/todos/{t1['id']}", headers=headers_a)).json()
    check_t2 = (await client.get(f"/api/v1/todos/{t2['id']}", headers=headers_a)).json()
    assert check_t1["completed"] is True
    assert check_t2["completed"] is True

    # IDOR Test: User A attempts to bulk update [t1, tb] (tb belongs to User B)
    # The whole transaction MUST abort with 403 Forbidden
    idor_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1["id"], tb["id"]], "completed": False},
        headers=headers_a,
    )
    assert idor_res.status_code == 403

    # Verify t1 was NOT modified (transaction rollback integrity)
    check_t1_after = (await client.get(f"/api/v1/todos/{t1['id']}", headers=headers_a)).json()
    assert check_t1_after["completed"] is True


@pytest.mark.asyncio
async def test_cache_invalidation_on_tag_and_bulk_operations(client: AsyncClient, fake_redis):
    """Test that Redis cache is properly invalidated on tag attach/detach and bulk update."""
    token = await get_auth_token(client, "cache_tag_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    todo = (await client.post("/api/v1/todos", json={"title": "Cache Test Todo"}, headers=headers)).json()
    tag = (await client.post("/api/v1/tags", json={"name": "Cache Tag"}, headers=headers)).json()

    fake_redis.delete_pattern.reset_mock()

    # Attach tag -> triggers cache invalidation
    await client.post(f"/api/v1/todos/{todo['id']}/tags", json={"tag_id": tag["id"]}, headers=headers)
    assert fake_redis.delete_pattern.called

    fake_redis.delete_pattern.reset_mock()

    # Bulk status update -> triggers cache invalidation
    await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [todo["id"]], "completed": True},
        headers=headers,
    )
    assert fake_redis.delete_pattern.called
