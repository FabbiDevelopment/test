"""Tag & filter tests — Level 4 backend test coverage."""

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_get_token, mock_redis


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    token = await register_and_get_token(client, "tag-create@example.com")
    response = await client.post(
        "/api/v1/tags",
        json={"name": "Work", "color": "#ff0000"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Work"


@pytest.mark.asyncio
async def test_duplicate_tag_case_insensitive(client: AsyncClient):
    """Tag name unique per user, case-insensitive."""
    token = await register_and_get_token(client, "tag-dup@example.com")
    await client.post(
        "/api/v1/tags",
        json={"name": "Work"},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.post(
        "/api/v1/tags",
        json={"name": "work"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_cross_user_tag_access_forbidden(client: AsyncClient):
    token_a = await register_and_get_token(client, "tag-usera@example.com")
    token_b = await register_and_get_token(client, "tag-userb@example.com")

    create = await client.post(
        "/api/v1/tags",
        json={"name": "Private"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    tag_id = create.json()["id"]

    response = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Hacked"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_attach_other_users_tag_forbidden(client: AsyncClient):
    token_a = await register_and_get_token(client, "attach-a@example.com")
    token_b = await register_and_get_token(client, "attach-b@example.com")

    tag_b = await client.post(
        "/api/v1/tags",
        json={"name": "B-Tag"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    todo_a = await client.post(
        "/api/v1/todos",
        json={"title": "A Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await client.post(
        f"/api/v1/todos/{todo_a.json()['id']}/tags",
        json={"tag_id": tag_b.json()["id"]},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_filter_todos_by_tag(client: AsyncClient):
    token = await register_and_get_token(client, "filter-tag@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    tag = await client.post("/api/v1/tags", json={"name": "Urgent"}, headers=headers)
    tag_id = tag.json()["id"]

    t1 = await client.post("/api/v1/todos", json={"title": "Tagged Todo"}, headers=headers)
    t2 = await client.post("/api/v1/todos", json={"title": "Untagged Todo"}, headers=headers)

    await client.post(
        f"/api/v1/todos/{t1.json()['id']}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )

    filtered = await client.get(f"/api/v1/todos?tag_id={tag_id}", headers=headers)
    assert filtered.status_code == 200
    titles = [i["title"] for i in filtered.json()["items"]]
    assert "Tagged Todo" in titles
    assert "Untagged Todo" not in titles


@pytest.mark.asyncio
async def test_bulk_status_ownership_check(client: AsyncClient):
    token_a = await register_and_get_token(client, "bulk-a@example.com")
    token_b = await register_and_get_token(client, "bulk-b@example.com")

    todo_b = await client.post(
        "/api/v1/todos",
        json={"title": "B Todo"},
        headers={"Authorization": f"Bearer {token_b}"},
    )

    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [todo_b.json()["id"]], "completed": True},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_tag_mutation_invalidates_cache(client: AsyncClient):
    token = await register_and_get_token(client, "tag-cache@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    user_id = me.json()["id"]

    import json
    mock_redis._store[f"todos:list:{user_id}:1:20:00000000"] = json.dumps(
        {"items": [], "total": 0, "page": 1, "size": 20}
    )

    await client.post("/api/v1/tags", json={"name": "CacheTest"}, headers=headers)

    # THÊM: POST /tags phải gọi delete_by_prefix — invalidate mọi cache list của user
    remaining = [k for k in mock_redis._store if k.startswith(f"todos:list:{user_id}:")]
    assert len(remaining) == 0
