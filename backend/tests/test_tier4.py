import pytest
from httpx import AsyncClient


async def token_for(client: AsyncClient, email: str) -> str:
    response = await client.post("/api/v1/auth/register", json={"email": email, "password": "password123"})
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_tag_names_are_unique_case_insensitively(client: AsyncClient):
    token = await token_for(client, "tags@example.com")
    first = await client.post("/api/v1/tags", json={"name": "Work", "color": "#2563eb"}, headers=headers(token))
    duplicate = await client.post("/api/v1/tags", json={"name": "work"}, headers=headers(token))
    assert first.status_code == 201
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_attach_and_filter_by_owned_tag(client: AsyncClient):
    token = await token_for(client, "filter@example.com")
    tag = (await client.post("/api/v1/tags", json={"name": "Urgent"}, headers=headers(token))).json()
    todo = (await client.post("/api/v1/todos", json={"title": "Release app"}, headers=headers(token))).json()
    await client.post("/api/v1/todos", json={"title": "Buy milk"}, headers=headers(token))

    attached = await client.post(f"/api/v1/todos/{todo['id']}/tags", json={"tag_id": tag["id"]}, headers=headers(token))
    filtered = await client.get("/api/v1/todos", params={"tag_id": tag["id"], "keyword": "release", "status": "active"}, headers=headers(token))

    assert attached.status_code == 200
    assert attached.json()["tags"][0]["name"] == "Urgent"
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [todo["id"]]


@pytest.mark.asyncio
async def test_cannot_attach_another_users_tag(client: AsyncClient):
    owner = await token_for(client, "owner-tag@example.com")
    attacker = await token_for(client, "attacker-tag@example.com")
    tag = (await client.post("/api/v1/tags", json={"name": "Private"}, headers=headers(owner))).json()
    todo = (await client.post("/api/v1/todos", json={"title": "Mine"}, headers=headers(attacker))).json()

    response = await client.post(f"/api/v1/todos/{todo['id']}/tags", json={"tag_id": tag["id"]}, headers=headers(attacker))
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_status_is_atomic_for_owned_todos(client: AsyncClient):
    owner = await token_for(client, "bulk-owner@example.com")
    other = await token_for(client, "bulk-other@example.com")
    mine = (await client.post("/api/v1/todos", json={"title": "Mine"}, headers=headers(owner))).json()
    foreign = (await client.post("/api/v1/todos", json={"title": "Foreign"}, headers=headers(other))).json()

    rejected = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [mine["id"], foreign["id"]], "completed": True}, headers=headers(owner))
    current = await client.get(f"/api/v1/todos/{mine['id']}", headers=headers(owner))

    assert rejected.status_code == 404
    assert current.json()["completed"] is False

    accepted = await client.patch("/api/v1/todos/bulk-status", json={"todo_ids": [mine["id"]], "completed": True}, headers=headers(owner))
    assert accepted.status_code == 200
    assert accepted.json()[0]["completed"] is True