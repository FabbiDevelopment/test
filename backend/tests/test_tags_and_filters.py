from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock

from app.api.deps import get_redis
from app.core.config import settings
from app.main import app


async def create_account(client: AsyncClient, email: str) -> dict[str, str]:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def create_tag(
    client: AsyncClient,
    headers: dict[str, str],
    name: str,
    color: str | None = None,
) -> dict:
    response = await client.post(
        "/api/v1/tags",
        json={"name": name, "color": color},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


async def create_todo(
    client: AsyncClient, headers: dict[str, str], title: str, description: str = ""
) -> dict:
    response = await client.post(
        "/api/v1/todos",
        json={"title": title, "description": description},
        headers=headers,
    )
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_tag_crud_and_case_insensitive_uniqueness(client: AsyncClient):
    owner = await create_account(client, "tag-owner@example.com")
    other = await create_account(client, "tag-other@example.com")

    tag = await create_tag(client, owner, "  Work  ", "blue")
    assert tag["name"] == "Work"
    assert tag["color"] == "blue"

    duplicate = await client.post("/api/v1/tags", json={"name": "work"}, headers=owner)
    assert duplicate.status_code == 409

    same_name_for_other_user = await client.post(
        "/api/v1/tags", json={"name": "WORK"}, headers=other
    )
    assert same_name_for_other_user.status_code == 201

    listed = await client.get("/api/v1/tags", headers=owner)
    assert [item["id"] for item in listed.json()["items"]] == [tag["id"]]

    renamed = await client.patch(
        f"/api/v1/tags/{tag['id']}",
        json={"name": "Personal", "color": None},
        headers=owner,
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Personal"
    assert renamed.json()["color"] is None

    hidden = await client.patch(
        f"/api/v1/tags/{tag['id']}", json={"name": "Stolen"}, headers=other
    )
    assert hidden.status_code == 404
    deleted = await client.delete(f"/api/v1/tags/{tag['id']}", headers=owner)
    assert deleted.status_code == 204


@pytest.mark.asyncio
async def test_todo_filters_status_tag_keyword_date_and_cache_keys(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    cached_keys: list[str] = []
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)

    async def record_cache(key: str, value: str, ex=None):
        cached_keys.append(key)

    redis.set = AsyncMock(side_effect=record_cache)
    redis.delete_pattern = AsyncMock()
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)

    owner = await create_account(client, "filter-owner@example.com")
    other = await create_account(client, "filter-other@example.com")
    work = await create_tag(client, owner, "Work")
    foreign_tag = await create_tag(client, other, "Private")

    alpha = await create_todo(client, owner, "Alpha project", "release notes")
    beta = await create_todo(client, owner, "Beta errands", "shopping")
    await client.put(
        f"/api/v1/todos/{beta['id']}", json={"completed": True}, headers=owner
    )
    attached = await client.post(
        f"/api/v1/todos/{alpha['id']}/tags",
        json={"tag_id": work["id"]},
        headers=owner,
    )
    assert attached.status_code == 201

    by_status = await client.get(
        "/api/v1/todos", params={"status": "completed"}, headers=owner
    )
    assert [item["id"] for item in by_status.json()["items"]] == [beta["id"]]

    by_tag = await client.get(
        "/api/v1/todos", params={"tag_id": work["id"]}, headers=owner
    )
    assert [item["id"] for item in by_tag.json()["items"]] == [alpha["id"]]
    assert by_tag.json()["items"][0]["tags"][0]["name"] == "Work"

    by_keyword = await client.get(
        "/api/v1/todos", params={"keyword": "RELEASE"}, headers=owner
    )
    assert [item["id"] for item in by_keyword.json()["items"]] == [alpha["id"]]

    created_at = datetime.fromisoformat(alpha["created_at"])
    if created_at.tzinfo is None:
        # SQLite drops timezone metadata; model timestamps are still stored in UTC.
        created_at = created_at.replace(tzinfo=timezone.utc)
    local_created_date = created_at.astimezone(
        timezone(timedelta(hours=settings.APP_UTC_OFFSET_HOURS))
    ).date().isoformat()
    by_date = await client.get(
        "/api/v1/todos",
        params={
            "date_from": local_created_date,
            "date_to": local_created_date,
            "page_size": 1,
        },
        headers=owner,
    )
    assert by_date.status_code == 200
    assert by_date.json()["size"] == 1
    assert by_date.json()["total"] == 2

    hidden_tag = await client.get(
        "/api/v1/todos", params={"tag_id": foreign_tag["id"]}, headers=owner
    )
    assert hidden_tag.status_code == 404

    invalid_date_format = await client.get(
        "/api/v1/todos",
        params={"date_from": "03-10-2026"},
        headers=owner,
    )
    assert invalid_date_format.status_code == 422

    invalid_range = await client.get(
        "/api/v1/todos",
        params={"date_from": "2026-10-03", "date_to": "2026-10-02"},
        headers=owner,
    )
    assert invalid_range.status_code == 422

    assert len(cached_keys) >= 4
    assert len(set(cached_keys)) == len(cached_keys)
    assert all("todos:" in key and "list:" in key for key in cached_keys)


@pytest.mark.asyncio
async def test_tag_attachment_ownership_detach_and_delete_cascade(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete_pattern = AsyncMock()
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)

    owner = await create_account(client, "mapping-owner@example.com")
    other = await create_account(client, "mapping-other@example.com")
    todo = await create_todo(client, owner, "Tagged todo")
    own_tag = await create_tag(client, owner, "Own")
    foreign_tag = await create_tag(client, other, "Foreign")

    foreign_todo = await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": foreign_tag["id"]},
        headers=owner,
    )
    assert foreign_todo.status_code == 404

    attach = await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": own_tag["id"]},
        headers=owner,
    )
    assert attach.status_code == 201
    duplicate = await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": own_tag["id"]},
        headers=owner,
    )
    assert duplicate.status_code == 409

    listing = await client.get("/api/v1/todos", headers=owner)
    assert listing.json()["items"][0]["tags"][0]["id"] == own_tag["id"]

    detach = await client.delete(
        f"/api/v1/todos/{todo['id']}/tags/{own_tag['id']}", headers=owner
    )
    assert detach.status_code == 204
    missing_mapping = await client.delete(
        f"/api/v1/todos/{todo['id']}/tags/{own_tag['id']}", headers=owner
    )
    assert missing_mapping.status_code == 404

    await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": own_tag["id"]},
        headers=owner,
    )
    assert (
        await client.delete(f"/api/v1/tags/{own_tag['id']}", headers=owner)
    ).status_code == 204
    refreshed = await client.get(f"/api/v1/todos/{todo['id']}", headers=owner)
    assert refreshed.status_code == 200
    assert refreshed.json()["tags"] == []
    assert redis.delete_pattern.await_count >= 4


@pytest.mark.asyncio
async def test_bulk_status_is_atomic_owner_scoped_and_invalidates_cache(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.delete_pattern = AsyncMock()
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)

    owner = await create_account(client, "bulk-owner@example.com")
    other = await create_account(client, "bulk-other@example.com")
    first = await create_todo(client, owner, "First")
    second = await create_todo(client, owner, "Second")
    foreign = await create_todo(client, other, "Foreign")

    updated = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], second["id"]], "completed": True},
        headers=owner,
    )
    assert updated.status_code == 200
    assert updated.json() == {"updated": 2}
    for todo in (first, second):
        detail = await client.get(f"/api/v1/todos/{todo['id']}", headers=owner)
        assert detail.json()["completed"] is True

    denied = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], foreign["id"]], "completed": False},
        headers=owner,
    )
    assert denied.status_code == 404
    still_completed = await client.get(f"/api/v1/todos/{first['id']}", headers=owner)
    assert still_completed.json()["completed"] is True
    assert redis.delete_pattern.await_args_list[-1].args == (
        f"todos:{first['user_id']}:list:*",
    )

    duplicate_ids = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], first["id"]], "completed": False},
        headers=owner,
    )
    assert duplicate_ids.status_code == 422
