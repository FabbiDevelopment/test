"""Tag tests."""
import pytest
from httpx import AsyncClient

async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    response = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    return response.json()["access_token"]

@pytest.mark.asyncio
async def test_create_tag(client: AsyncClient):
    token = await get_auth_token(client, "tag_create@example.com")
    response = await client.post("/api/v1/tags", json={"name": "Work", "color": "#ff0000"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["name"] == "Work"
    assert response.json()["color"] == "#ff0000"

@pytest.mark.asyncio
async def test_create_duplicate_tag_case_insensitive(client: AsyncClient):
    token = await get_auth_token(client, "tag_dup@example.com")
    await client.post("/api/v1/tags", json={"name": "Work"}, headers={"Authorization": f"Bearer {token}"})
    response = await client.post("/api/v1/tags", json={"name": "work"}, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 400

@pytest.mark.asyncio
async def test_list_tags(client: AsyncClient):
    token = await get_auth_token(client, "tag_list@example.com")
    await client.post("/api/v1/tags", json={"name": "T1"}, headers={"Authorization": f"Bearer {token}"})
    await client.post("/api/v1/tags", json={"name": "T2"}, headers={"Authorization": f"Bearer {token}"})
    response = await client.get("/api/v1/tags", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert len(response.json()) >= 2

@pytest.mark.asyncio
async def test_update_tag(client: AsyncClient):
    token = await get_auth_token(client, "tag_update@example.com")
    create_res = await client.post("/api/v1/tags", json={"name": "Old"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = create_res.json()["id"]
    update_res = await client.patch(f"/api/v1/tags/{tag_id}", json={"name": "New"}, headers={"Authorization": f"Bearer {token}"})
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "New"

@pytest.mark.asyncio
async def test_delete_tag(client: AsyncClient):
    token = await get_auth_token(client, "tag_delete@example.com")
    create_res = await client.post("/api/v1/tags", json={"name": "Del"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = create_res.json()["id"]
    del_res = await client.delete(f"/api/v1/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert del_res.status_code == 204
    get_res = await client.get("/api/v1/tags", headers={"Authorization": f"Bearer {token}"})
    assert len(get_res.json()) == 0

@pytest.mark.asyncio
async def test_cross_user_tag_access(client: AsyncClient):
    token_a = await get_auth_token(client, "tag_usera@example.com")
    token_b = await get_auth_token(client, "tag_userb@example.com")
    create_res = await client.post("/api/v1/tags", json={"name": "A Tag"}, headers={"Authorization": f"Bearer {token_a}"})
    tag_id = create_res.json()["id"]
    update_res = await client.patch(f"/api/v1/tags/{tag_id}", json={"name": "Hacked"}, headers={"Authorization": f"Bearer {token_b}"})
    assert update_res.status_code == 404
    del_res = await client.delete(f"/api/v1/tags/{tag_id}", headers={"Authorization": f"Bearer {token_b}"})
    assert del_res.status_code == 404

@pytest.mark.asyncio
async def test_attach_tag_to_todo(client: AsyncClient):
    token = await get_auth_token(client, "tag_attach@example.com")
    todo_res = await client.post("/api/v1/todos", json={"title": "Todo 1"}, headers={"Authorization": f"Bearer {token}"})
    todo_id = todo_res.json()["id"]
    tag_res = await client.post("/api/v1/tags", json={"name": "Tag 1"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = tag_res.json()["id"]
    attach_res = await client.post(f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers={"Authorization": f"Bearer {token}"})
    assert attach_res.status_code == 201

@pytest.mark.asyncio
async def test_attach_other_user_tag(client: AsyncClient):
    token_a = await get_auth_token(client, "att_usera@example.com")
    token_b = await get_auth_token(client, "att_userb@example.com")
    todo_res = await client.post("/api/v1/todos", json={"title": "A's Todo"}, headers={"Authorization": f"Bearer {token_a}"})
    todo_id = todo_res.json()["id"]
    tag_res = await client.post("/api/v1/tags", json={"name": "B's Tag"}, headers={"Authorization": f"Bearer {token_b}"})
    tag_id = tag_res.json()["id"]
    attach_res = await client.post(f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers={"Authorization": f"Bearer {token_a}"})
    assert attach_res.status_code == 404

@pytest.mark.asyncio
async def test_detach_tag_from_todo(client: AsyncClient):
    token = await get_auth_token(client, "tag_detach@example.com")
    todo_res = await client.post("/api/v1/todos", json={"title": "Todo D"}, headers={"Authorization": f"Bearer {token}"})
    todo_id = todo_res.json()["id"]
    tag_res = await client.post("/api/v1/tags", json={"name": "Tag D"}, headers={"Authorization": f"Bearer {token}"})
    tag_id = tag_res.json()["id"]
    await client.post(f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers={"Authorization": f"Bearer {token}"})
    detach_res = await client.delete(f"/api/v1/todos/{todo_id}/tags/{tag_id}", headers={"Authorization": f"Bearer {token}"})
    assert detach_res.status_code == 204

@pytest.mark.asyncio
async def test_bulk_update_status(client: AsyncClient):
    token = await get_auth_token(client, "bulk_update@example.com")
    t1 = await client.post("/api/v1/todos", json={"title": "T1"}, headers={"Authorization": f"Bearer {token}"})
    t2 = await client.post("/api/v1/todos", json={"title": "T2"}, headers={"Authorization": f"Bearer {token}"})
    id1, id2 = t1.json()["id"], t2.json()["id"]
    res = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [id1, id2], "completed": True}, headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.json()["updated_count"] == 2
    get1 = await client.get(f"/api/v1/todos/{id1}", headers={"Authorization": f"Bearer {token}"})
    assert get1.json()["completed"] is True

@pytest.mark.asyncio
async def test_bulk_update_cross_user(client: AsyncClient):
    token_a = await get_auth_token(client, "bulk_usera@example.com")
    token_b = await get_auth_token(client, "bulk_userb@example.com")
    t1 = await client.post("/api/v1/todos", json={"title": "T1"}, headers={"Authorization": f"Bearer {token_a}"})
    id1 = t1.json()["id"]
    res = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [id1], "completed": True}, headers={"Authorization": f"Bearer {token_b}"})
    assert res.status_code == 400
