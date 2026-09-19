import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    register_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "tag_user@test.com", "password": "Password@123"},
    )
    token = register_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#3B82F6"},
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Work"
    assert data["color"] == "#3B82F6"


@pytest.mark.asyncio
async def test_duplicate_tag_casing_rejected(client: AsyncClient):
    register_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "dup_tag_user@test.com", "password": "Password@123"},
    )
    token = register_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res1 = await client.post(
        "/api/v1/tags",
        json={"name": "Urgent", "color": "#EF4444"},
        headers=headers,
    )
    assert res1.status_code == 201

    res2 = await client.post(
        "/api/v1/tags",
        json={"name": "urgent", "color": "#10B981"},
        headers=headers,
    )
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_attach_detach_tag_and_filtering(client: AsyncClient):
    register_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "filter_user@test.com", "password": "Password@123"},
    )
    token = register_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "Personal", "color": "#8B5CF6"},
        headers=headers,
    )
    tag_id = tag_res.json()["id"]

    todo1_res = await client.post(
        "/api/v1/todos",
        json={"title": "Buy groceries", "description": "Milk and eggs"},
        headers=headers,
    )
    todo1_id = todo1_res.json()["id"]

    todo2_res = await client.post(
        "/api/v1/todos",
        json={"title": "Finish report", "description": "Quarterly report"},
        headers=headers,
    )
    todo2_id = todo2_res.json()["id"]

    attach_res = await client.post(
        f"/api/v1/todos/{todo1_id}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )
    assert attach_res.status_code == 200
    assert len(attach_res.json()["tags"]) == 1
    assert attach_res.json()["tags"][0]["name"] == "Personal"

    filter_res = await client.get(
        f"/api/v1/todos?tag_id={tag_id}",
        headers=headers,
    )
    assert filter_res.status_code == 200
    items = filter_res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == todo1_id

    
    kw_res = await client.get(
        "/api/v1/todos?keyword=report",
        headers=headers,
    )
    assert kw_res.status_code == 200
    kw_items = kw_res.json()["items"]
    assert len(kw_items) == 1
    assert kw_items[0]["id"] == todo2_id


    detach_res = await client.delete(
        f"/api/v1/todos/{todo1_id}/tags/{tag_id}",
        headers=headers,
    )
    assert detach_res.status_code == 200
    assert len(detach_res.json()["tags"]) == 0


@pytest.mark.asyncio
async def test_bulk_status_update(client: AsyncClient):
    register_res = await client.post(
        "/api/v1/auth/register",
        json={"email": "bulk_user@test.com", "password": "Password@123"},
    )
    token = register_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    
    t1 = (await client.post("/api/v1/todos", json={"title": "Task 1"}, headers=headers)).json()["id"]
    t2 = (await client.post("/api/v1/todos", json={"title": "Task 2"}, headers=headers)).json()["id"]
    t3 = (await client.post("/api/v1/todos", json={"title": "Task 3"}, headers=headers)).json()["id"]

    
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1, t2], "completed": True},
        headers=headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2

    get1 = (await client.get(f"/api/v1/todos/{t1}", headers=headers)).json()
    get3 = (await client.get(f"/api/v1/todos/{t3}", headers=headers)).json()
    assert get1["completed"] is True
    assert get3["completed"] is False
