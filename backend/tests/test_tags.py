from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_redis
from app.main import app


async def register(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "Password@123"},
    )
    return response.json()["access_token"]


def headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_tag_and_reject_case_insensitive_duplicate(client: AsyncClient):
    token = await register(client, "tags@example.com")
    first = await client.post(
        "/api/v1/tags",
        json={"name": "Urgent", "color": "#ef4444"},
        headers=headers(token),
    )
    duplicate = await client.post(
        "/api/v1/tags", json={"name": "urgent"}, headers=headers(token)
    )

    assert first.status_code == 201
    assert first.json()["name"] == "Urgent"
    assert duplicate.status_code == 409


@pytest.mark.asyncio
async def test_user_cannot_update_another_users_tag(client: AsyncClient):
    owner = await register(client, "tag-owner@example.com")
    other = await register(client, "tag-other@example.com")
    tag = (
        await client.post(
            "/api/v1/tags", json={"name": "Private"}, headers=headers(owner)
        )
    ).json()

    response = await client.patch(
        f"/api/v1/tags/{tag['id']}",
        json={"name": "Stolen"},
        headers=headers(other),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_attach_own_tag_and_filter_todos_by_tag(client: AsyncClient):
    token = await register(client, "filter-tag@example.com")
    auth = headers(token)
    tag = (
        await client.post("/api/v1/tags", json={"name": "Work"}, headers=auth)
    ).json()
    tagged = (
        await client.post("/api/v1/todos", json={"title": "Tagged"}, headers=auth)
    ).json()
    await client.post("/api/v1/todos", json={"title": "Plain"}, headers=auth)

    attach = await client.post(
        f"/api/v1/todos/{tagged['id']}/tags",
        json={"tag_id": tag["id"]},
        headers=auth,
    )
    filtered = await client.get(
        "/api/v1/todos", params={"tag_id": tag["id"]}, headers=auth
    )

    assert attach.status_code == 200
    assert [item["name"] for item in attach.json()["tags"]] == ["Work"]
    assert [item["title"] for item in filtered.json()["items"]] == ["Tagged"]


@pytest.mark.asyncio
async def test_cannot_attach_another_users_tag(client: AsyncClient):
    owner = await register(client, "attach-owner@example.com")
    other = await register(client, "attach-other@example.com")
    todo = (
        await client.post(
            "/api/v1/todos", json={"title": "Mine"}, headers=headers(owner)
        )
    ).json()
    foreign_tag = (
        await client.post(
            "/api/v1/tags", json={"name": "Foreign"}, headers=headers(other)
        )
    ).json()

    response = await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": foreign_tag["id"]},
        headers=headers(owner),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_bulk_status_rejects_mixed_ownership_without_partial_update(
    client: AsyncClient,
):
    owner = await register(client, "bulk-owner@example.com")
    other = await register(client, "bulk-other@example.com")
    own_todo = (
        await client.post(
            "/api/v1/todos", json={"title": "Own"}, headers=headers(owner)
        )
    ).json()
    foreign_todo = (
        await client.post(
            "/api/v1/todos", json={"title": "Foreign"}, headers=headers(other)
        )
    ).json()

    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={
            "todo_ids": [own_todo["id"], foreign_todo["id"]],
            "completed": True,
        },
        headers=headers(owner),
    )
    persisted = await client.get(
        f"/api/v1/todos/{own_todo['id']}", headers=headers(owner)
    )

    assert response.status_code == 404
    assert persisted.json()["completed"] is False


@pytest.mark.asyncio
async def test_filter_by_keyword_status_and_date_and_bulk_update(client: AsyncClient):
    token = await register(client, "combined-filter@example.com")
    auth = headers(token)
    matching = (
        await client.post(
            "/api/v1/todos",
            json={"title": "Quarterly report", "description": "finance"},
            headers=auth,
        )
    ).json()
    await client.post("/api/v1/todos", json={"title": "Personal errand"}, headers=auth)

    bulk = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [matching["id"]], "completed": True},
        headers=auth,
    )
    filtered = await client.get(
        "/api/v1/todos",
        params={
            "status": "completed",
            "keyword": "finance",
            "date_from": matching["created_at"],
            "date_to": matching["created_at"],
        },
        headers=auth,
    )

    assert bulk.status_code == 200
    assert bulk.json()["updated"] == 1
    assert [item["id"] for item in filtered.json()["items"]] == [matching["id"]]


@pytest.mark.asyncio
async def test_mutations_invalidate_user_scoped_todo_cache(client: AsyncClient):
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete_pattern = AsyncMock()
    previous = app.dependency_overrides[get_redis]
    app.dependency_overrides[get_redis] = lambda: redis

    try:
        token = await register(client, "invalidate@example.com")
        auth = headers(token)
        todo = (
            await client.post(
                "/api/v1/todos", json={"title": "Invalidate"}, headers=auth
            )
        ).json()
        await client.patch(
            "/api/v1/todos/bulk-status",
            json={"todo_ids": [todo["id"]], "completed": True},
            headers=auth,
        )

        assert redis.delete_pattern.await_count == 2
        redis.delete_pattern.assert_awaited_with(f"todos:{todo['user_id']}:*")
    finally:
        app.dependency_overrides[get_redis] = previous
