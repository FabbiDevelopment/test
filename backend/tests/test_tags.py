"""Tag, filter, and bulk-action regression tests for the Tier 4 extension."""

import pytest
from httpx import AsyncClient


async def register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def create_todo(client: AsyncClient, token: str, title: str) -> str:
    response = await client.post("/api/v1/todos", json={"title": title}, headers=headers(token))
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_tag_create_and_case_insensitive_duplicate(client: AsyncClient):
    token = await register(client, "tag-owner@example.com")

    created = await client.post(
        "/api/v1/tags", json={"name": "Work", "color": "blue"}, headers=headers(token)
    )
    assert created.status_code == 201
    assert created.json()["name"] == "Work"

    duplicate = await client.post(
        "/api/v1/tags", json={"name": "work"}, headers=headers(token)
    )
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_user_cannot_attach_another_users_tag(client: AsyncClient):
    owner = await register(client, "tag-owner-a@example.com")
    other = await register(client, "tag-owner-b@example.com")
    tag = await client.post("/api/v1/tags", json={"name": "Private"}, headers=headers(owner))
    todo_id = await create_todo(client, other, "Other user's todo")

    response = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag.json()["id"]},
        headers=headers(other),
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tag_filter_and_detach_invalidate_cached_list(client: AsyncClient):
    token = await register(client, "tag-filter@example.com")
    tagged_todo = await create_todo(client, token, "Tagged todo")
    await create_todo(client, token, "Untagged todo")
    tag = await client.post("/api/v1/tags", json={"name": "Filter"}, headers=headers(token))
    tag_id = tag.json()["id"]

    attached = await client.post(
        f"/api/v1/todos/{tagged_todo}/tags", json={"tag_id": tag_id}, headers=headers(token)
    )
    assert attached.status_code == 201

    filtered = await client.get(f"/api/v1/todos?tag_id={tag_id}", headers=headers(token))
    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()["items"]] == [tagged_todo]

    detached = await client.delete(
        f"/api/v1/todos/{tagged_todo}/tags/{tag_id}", headers=headers(token)
    )
    assert detached.status_code == 204

    refreshed = await client.get(f"/api/v1/todos?tag_id={tag_id}", headers=headers(token))
    assert refreshed.json()["total"] == 0


@pytest.mark.asyncio
async def test_bulk_update_rejects_mixed_ownership_without_partial_write(client: AsyncClient):
    owner = await register(client, "bulk-owner@example.com")
    other = await register(client, "bulk-other@example.com")
    owner_todo = await create_todo(client, owner, "Owner todo")
    other_todo = await create_todo(client, other, "Other todo")

    rejected = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [owner_todo, other_todo], "completed": True},
        headers=headers(owner),
    )
    assert rejected.status_code == 403
    unchanged = await client.get(f"/api/v1/todos/{owner_todo}", headers=headers(owner))
    assert unchanged.json()["completed"] is False

    updated = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [owner_todo], "completed": True},
        headers=headers(owner),
    )
    assert updated.status_code == 200
    assert updated.json()[0]["completed"] is True
