"""Bonus tag, filtering, bulk update, and cache tests."""

import pytest
from httpx import AsyncClient


async def register_headers(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def create_todo(
    client: AsyncClient,
    headers: dict[str, str],
    title: str,
) -> dict:
    response = await client.post(
        "/api/v1/todos",
        json={"title": title, "description": f"Description for {title}"},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def create_tag(
    client: AsyncClient,
    headers: dict[str, str],
    name: str,
    color: str = "#2563eb",
) -> dict:
    response = await client.post(
        "/api/v1/tags",
        json={"name": name, "color": color},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_tag_crud_case_insensitive_unique_and_ownership(client: AsyncClient):
    owner_headers = await register_headers(client, "tag-owner@example.com")
    other_headers = await register_headers(client, "tag-other@example.com")

    tag = await create_tag(client, owner_headers, "Work")

    duplicate = await client.post(
        "/api/v1/tags",
        json={"name": "work", "color": "#000000"},
        headers=owner_headers,
    )
    assert duplicate.status_code == 409

    owner_list = await client.get("/api/v1/tags", headers=owner_headers)
    other_list = await client.get("/api/v1/tags", headers=other_headers)
    assert [item["id"] for item in owner_list.json()] == [tag["id"]]
    assert other_list.json() == []

    forbidden_update = await client.patch(
        f"/api/v1/tags/{tag['id']}",
        json={"name": "Stolen"},
        headers=other_headers,
    )
    forbidden_delete = await client.delete(
        f"/api/v1/tags/{tag['id']}",
        headers=other_headers,
    )
    assert forbidden_update.status_code == 404
    assert forbidden_delete.status_code == 404

    update = await client.patch(
        f"/api/v1/tags/{tag['id']}",
        json={"name": "Priority", "color": "#dc2626"},
        headers=owner_headers,
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Priority"

    delete = await client.delete(
        f"/api/v1/tags/{tag['id']}",
        headers=owner_headers,
    )
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_attach_filter_and_reject_another_users_tag(client: AsyncClient):
    owner_headers = await register_headers(client, "filter-owner@example.com")
    other_headers = await register_headers(client, "filter-other@example.com")

    work_tag = await create_tag(client, owner_headers, "Work")
    other_tag = await create_tag(client, other_headers, "Private")
    alpha = await create_todo(client, owner_headers, "Alpha release")
    beta = await create_todo(client, owner_headers, "Beta planning")

    attach = await client.post(
        f"/api/v1/todos/{alpha['id']}/tags",
        json={"tag_id": work_tag["id"]},
        headers=owner_headers,
    )
    assert attach.status_code == 200
    assert [tag["id"] for tag in attach.json()["tags"]] == [work_tag["id"]]

    cross_user_attach = await client.post(
        f"/api/v1/todos/{alpha['id']}/tags",
        json={"tag_id": other_tag["id"]},
        headers=owner_headers,
    )
    assert cross_user_attach.status_code == 404

    completed = await client.put(
        f"/api/v1/todos/{alpha['id']}",
        json={"completed": True},
        headers=owner_headers,
    )
    assert completed.status_code == 200

    filtered = await client.get(
        "/api/v1/todos",
        params={
            "status": "completed",
            "tag_id": work_tag["id"],
            "keyword": "alpha",
            "date_from": "2000-01-01T00:00:00Z",
            "date_to": "2100-01-01T00:00:00Z",
            "page": 1,
            "page_size": 10,
        },
        headers=owner_headers,
    )
    assert filtered.status_code == 200
    assert [todo["id"] for todo in filtered.json()["items"]] == [alpha["id"]]

    active = await client.get(
        "/api/v1/todos",
        params={"status": "active"},
        headers=owner_headers,
    )
    assert [todo["id"] for todo in active.json()["items"]] == [beta["id"]]

    future = await client.get(
        "/api/v1/todos",
        params={"date_from": "2100-01-01T00:00:00Z"},
        headers=owner_headers,
    )
    assert future.json()["items"] == []


@pytest.mark.asyncio
async def test_bulk_status_is_atomic_and_scoped_to_owner(client: AsyncClient):
    owner_headers = await register_headers(client, "bulk-owner@example.com")
    other_headers = await register_headers(client, "bulk-other@example.com")
    first = await create_todo(client, owner_headers, "First bulk todo")
    second = await create_todo(client, owner_headers, "Second bulk todo")
    foreign = await create_todo(client, other_headers, "Foreign todo")

    rejected = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], foreign["id"]], "completed": True},
        headers=owner_headers,
    )
    assert rejected.status_code == 404

    unchanged = await client.get(f"/api/v1/todos/{first['id']}", headers=owner_headers)
    assert unchanged.json()["completed"] is False

    updated = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], second["id"]], "completed": True},
        headers=owner_headers,
    )
    assert updated.status_code == 200
    assert updated.json()["updated_count"] == 2
    assert all(todo["completed"] for todo in updated.json()["items"])


@pytest.mark.asyncio
async def test_mutations_invalidate_user_todo_cache(client: AsyncClient, redis_mock):
    headers = await register_headers(client, "cache-bonus@example.com")
    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]
    expected_pattern = f"todos:{user_id}:list:*"

    todo = await create_todo(client, headers, "Cache todo")
    tag = await create_tag(client, headers, "Cache tag")
    await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": tag["id"]},
        headers=headers,
    )
    await client.delete(
        f"/api/v1/todos/{todo['id']}/tags/{tag['id']}",
        headers=headers,
    )
    await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [todo["id"]], "completed": True},
        headers=headers,
    )
    await client.delete(f"/api/v1/todos/{todo['id']}", headers=headers)

    assert redis_mock.delete_pattern.await_count == 5
    assert all(
        call.args == (expected_pattern,)
        for call in redis_mock.delete_pattern.await_args_list
    )
