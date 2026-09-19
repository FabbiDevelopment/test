"""Tags and Bulk Actions tests."""

import pytest
from httpx import AsyncClient

from tests.test_todos import create_authenticated_user


@pytest.mark.asyncio
async def test_create_and_list_tags(client: AsyncClient):
    """Test creating and listing tags."""
    token, _ = await create_authenticated_user(client, "tag_user1@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    create_res = await client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "Work", "color": "#ff0000"},
    )
    assert create_res.status_code == 201
    data = create_res.json()
    assert data["name"] == "Work"
    assert data["color"] == "#ff0000"

    list_res = await client.get("/api/v1/tags", headers=headers)
    assert list_res.status_code == 200
    tags = list_res.json()
    assert len(tags) == 1
    assert tags[0]["name"] == "Work"


@pytest.mark.asyncio
async def test_case_insensitive_unique_tag_name(client: AsyncClient):
    """Test duplicate tag name with different casing is rejected."""
    token, _ = await create_authenticated_user(client, "tag_user2@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "Urgent"},
    )

    # Attempt to create "urgent"
    dup_res = await client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "urgent"},
    )
    assert dup_res.status_code == 400
    assert "already exists" in dup_res.json()["detail"]


@pytest.mark.asyncio
async def test_cross_user_tag_isolation(client: AsyncClient):
    """Test User B cannot access or attach User A's tags."""
    token_a, _ = await create_authenticated_user(client, "user_tag_a@example.com")
    token_b, _ = await create_authenticated_user(client, "user_tag_b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates tag
    tag_a_res = await client.post(
        "/api/v1/tags",
        headers=headers_a,
        json={"name": "Confidential A"},
    )
    tag_a_id = tag_a_res.json()["id"]

    # User B creates todo
    todo_b_res = await client.post(
        "/api/v1/todos",
        headers=headers_b,
        json={"title": "Todo B"},
    )
    todo_b_id = todo_b_res.json()["id"]

    # User B tries to attach User A's tag -> 404
    attach_res = await client.post(
        f"/api/v1/todos/{todo_b_id}/tags",
        headers=headers_b,
        json={"tag_id": tag_a_id},
    )
    assert attach_res.status_code == 404


@pytest.mark.asyncio
async def test_attach_and_detach_tag(client: AsyncClient):
    """Test attaching and detaching a tag from a todo."""
    token, _ = await create_authenticated_user(client, "tag_attach_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    tag_res = await client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "Personal"},
    )
    tag_id = tag_res.json()["id"]

    todo_res = await client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Buy gift"},
    )
    todo_id = todo_res.json()["id"]

    # Attach tag
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        headers=headers,
        json={"tag_id": tag_id},
    )
    assert attach_res.status_code == 200
    assert len(attach_res.json()["tags"]) == 1
    assert attach_res.json()["tags"][0]["id"] == tag_id

    # Filter by tag
    filter_res = await client.get(f"/api/v1/todos?tag_id={tag_id}", headers=headers)
    assert filter_res.status_code == 200
    assert filter_res.json()["total"] == 1

    # Detach tag
    detach_res = await client.delete(
        f"/api/v1/todos/{todo_id}/tags/{tag_id}",
        headers=headers,
    )
    assert detach_res.status_code == 200
    assert len(detach_res.json()["tags"]) == 0


@pytest.mark.asyncio
async def test_bulk_status_update(client: AsyncClient):
    """Test bulk updating status of multiple todos."""
    token, _ = await create_authenticated_user(client, "bulk_user@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create 3 todos
    t1 = (await client.post("/api/v1/todos", headers=headers, json={"title": "T1"})).json()["id"]
    t2 = (await client.post("/api/v1/todos", headers=headers, json={"title": "T2"})).json()["id"]
    t3 = (await client.post("/api/v1/todos", headers=headers, json={"title": "T3"})).json()["id"]

    # Bulk complete t1 and t2
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        headers=headers,
        json={"todo_ids": [t1, t2], "completed": True},
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2

    # Check status
    res1 = (await client.get(f"/api/v1/todos/{t1}", headers=headers)).json()
    res2 = (await client.get(f"/api/v1/todos/{t2}", headers=headers)).json()
    res3 = (await client.get(f"/api/v1/todos/{t3}", headers=headers)).json()

    assert res1["completed"] is True
    assert res2["completed"] is True
    assert res3["completed"] is False
