import pytest
from httpx import AsyncClient

from tests.test_todos import get_auth_token


@pytest.mark.asyncio
async def test_tag_lifecycle_filter_and_case_insensitive_duplicate(client: AsyncClient):
    token = await get_auth_token(client, "tags@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created_tag = await client.post("/api/v1/tags", json={"name": "Work", "color": "#2563eb"}, headers=headers)
    assert created_tag.status_code == 201
    tag_id = created_tag.json()["id"]
    duplicate = await client.post("/api/v1/tags", json={"name": "work"}, headers=headers)
    assert duplicate.status_code == 409
    todo = await client.post("/api/v1/todos", json={"title": "Tagged todo"}, headers=headers)
    todo_id = todo.json()["id"]
    attached = await client.post(f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers=headers)
    assert attached.status_code == 200
    assert attached.json()["tags"][0]["name"] == "Work"
    filtered = await client.get("/api/v1/todos", params={"tag_id": tag_id}, headers=headers)
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [todo_id]


@pytest.mark.asyncio
async def test_user_cannot_attach_foreign_tag_or_bulk_update_foreign_todo(client: AsyncClient):
    token_a = await get_auth_token(client, "tag-a@example.com")
    token_b = await get_auth_token(client, "tag-b@example.com")
    headers_a, headers_b = {"Authorization": f"Bearer {token_a}"}, {"Authorization": f"Bearer {token_b}"}
    foreign_tag = await client.post("/api/v1/tags", json={"name": "Private"}, headers=headers_b)
    own_todo = await client.post("/api/v1/todos", json={"title": "Mine"}, headers=headers_a)
    foreign_todo = await client.post("/api/v1/todos", json={"title": "Theirs"}, headers=headers_b)
    attach = await client.post(f"/api/v1/todos/{own_todo.json()['id']}/tags", json={"tag_id": foreign_tag.json()['id']}, headers=headers_a)
    assert attach.status_code == 404
    bulk = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [own_todo.json()["id"], foreign_todo.json()["id"]], "completed": True}, headers=headers_a)
    assert bulk.status_code == 404
    unchanged = await client.get(f"/api/v1/todos/{own_todo.json()['id']}", headers=headers_a)
    assert unchanged.json()["completed"] is False
