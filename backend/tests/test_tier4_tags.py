"""Tier 4 (bonus): tags, filtering, and bulk actions.

Covers every scenario the README's "Suggested Tests" list calls out:
  - create tag success
  - duplicate tag casing
  - cross-user access prevention (tags)
  - attaching another user's tag prevention
  - filtering by tag
  - bulk update ownership check
  - cache invalidation
"""

import pytest
from httpx import AsyncClient

from tests.conftest import fake_redis


async def register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    response = await client.post(
        "/api/v1/auth/register", json={"email": email, "password": password}
    )
    assert response.status_code == 201, response.text
    return response.json()


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Tags: create / duplicate casing / cross-user access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    user = await register(client, "tag-create@example.com")
    headers = auth_header(user["access_token"])

    response = await client.post(
        "/api/v1/tags", json={"name": "Work", "color": "#ff0000"}, headers=headers
    )

    assert response.status_code == 201, response.text
    data = response.json()
    assert data["name"] == "Work"
    assert data["color"] == "#ff0000"


@pytest.mark.asyncio
async def test_duplicate_tag_name_case_insensitive_rejected(client: AsyncClient):
    user = await register(client, "tag-dup@example.com")
    headers = auth_header(user["access_token"])

    r1 = await client.post("/api/v1/tags", json={"name": "Urgent"}, headers=headers)
    assert r1.status_code == 201

    # Different casing of the same name must still collide.
    r2 = await client.post("/api/v1/tags", json={"name": "urgent"}, headers=headers)
    assert r2.status_code == 409

    r3 = await client.post("/api/v1/tags", json={"name": "URGENT"}, headers=headers)
    assert r3.status_code == 409


@pytest.mark.asyncio
async def test_two_different_users_can_each_have_same_tag_name(client: AsyncClient):
    """Uniqueness is per-user, not global."""
    user_a = await register(client, "tag-scope-a@example.com")
    user_b = await register(client, "tag-scope-b@example.com")

    r_a = await client.post(
        "/api/v1/tags", json={"name": "Personal"}, headers=auth_header(user_a["access_token"])
    )
    r_b = await client.post(
        "/api/v1/tags", json={"name": "Personal"}, headers=auth_header(user_b["access_token"])
    )

    assert r_a.status_code == 201
    assert r_b.status_code == 201


@pytest.mark.asyncio
async def test_cross_user_tag_access_prevented(client: AsyncClient):
    user_a = await register(client, "tag-owner@example.com")
    user_b = await register(client, "tag-intruder@example.com")

    create_resp = await client.post(
        "/api/v1/tags", json={"name": "Secret"}, headers=auth_header(user_a["access_token"])
    )
    tag_id = create_resp.json()["id"]

    # B cannot rename A's tag.
    rename_resp = await client.patch(
        f"/api/v1/tags/{tag_id}",
        json={"name": "Hijacked"},
        headers=auth_header(user_b["access_token"]),
    )
    assert rename_resp.status_code == 404

    # B cannot delete A's tag.
    delete_resp = await client.delete(
        f"/api/v1/tags/{tag_id}", headers=auth_header(user_b["access_token"])
    )
    assert delete_resp.status_code == 404

    # B's own tag list never contains A's tag.
    list_resp = await client.get("/api/v1/tags", headers=auth_header(user_b["access_token"]))
    assert all(t["id"] != tag_id for t in list_resp.json())


# ---------------------------------------------------------------------------
# Attaching another user's tag is prevented
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cannot_attach_another_users_tag(client: AsyncClient):
    user_a = await register(client, "attach-a@example.com")
    user_b = await register(client, "attach-b@example.com")
    headers_a = auth_header(user_a["access_token"])
    headers_b = auth_header(user_b["access_token"])

    # B has a tag, A has a todo.
    tag_resp = await client.post("/api/v1/tags", json={"name": "B's tag"}, headers=headers_b)
    tag_id = tag_resp.json()["id"]

    todo_resp = await client.post("/api/v1/todos", json={"title": "A's todo"}, headers=headers_a)
    todo_id = todo_resp.json()["id"]

    # A tries to attach B's tag to A's own todo.
    attach_resp = await client.post(
        f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers=headers_a
    )
    assert attach_resp.status_code == 404  # tag not found (not owned by A)


@pytest.mark.asyncio
async def test_cannot_attach_tag_to_another_users_todo(client: AsyncClient):
    user_a = await register(client, "attach2-a@example.com")
    user_b = await register(client, "attach2-b@example.com")
    headers_a = auth_header(user_a["access_token"])
    headers_b = auth_header(user_b["access_token"])

    todo_resp = await client.post("/api/v1/todos", json={"title": "A's todo"}, headers=headers_a)
    todo_id = todo_resp.json()["id"]

    tag_resp = await client.post("/api/v1/tags", json={"name": "B's tag"}, headers=headers_b)
    tag_id = tag_resp.json()["id"]

    # B tries to attach B's own tag to A's todo.
    attach_resp = await client.post(
        f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers=headers_b
    )
    assert attach_resp.status_code == 404  # todo not found (not owned by B)


@pytest.mark.asyncio
async def test_attach_and_detach_own_tag_succeeds(client: AsyncClient):
    user = await register(client, "attach-own@example.com")
    headers = auth_header(user["access_token"])

    tag_resp = await client.post("/api/v1/tags", json={"name": "Home"}, headers=headers)
    tag_id = tag_resp.json()["id"]

    todo_resp = await client.post("/api/v1/todos", json={"title": "Water plants"}, headers=headers)
    todo_id = todo_resp.json()["id"]

    attach_resp = await client.post(
        f"/api/v1/todos/{todo_id}/tags", json={"tag_id": tag_id}, headers=headers
    )
    assert attach_resp.status_code == 200
    assert [t["id"] for t in attach_resp.json()["tags"]] == [tag_id]

    detach_resp = await client.delete(f"/api/v1/todos/{todo_id}/tags/{tag_id}", headers=headers)
    assert detach_resp.status_code == 200
    assert detach_resp.json()["tags"] == []


# ---------------------------------------------------------------------------
# Filtering by tag
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_filter_todos_by_tag(client: AsyncClient):
    user = await register(client, "filter-tag@example.com")
    headers = auth_header(user["access_token"])

    tag_resp = await client.post("/api/v1/tags", json={"name": "Work"}, headers=headers)
    tag_id = tag_resp.json()["id"]

    tagged = await client.post("/api/v1/todos", json={"title": "Tagged"}, headers=headers)
    tagged_id = tagged.json()["id"]
    await client.post("/api/v1/todos", json={"title": "Untagged"}, headers=headers)

    await client.post(f"/api/v1/todos/{tagged_id}/tags", json={"tag_id": tag_id}, headers=headers)

    response = await client.get(f"/api/v1/todos?tag_id={tag_id}", headers=headers)
    items = response.json()["items"]

    assert len(items) == 1
    assert items[0]["id"] == tagged_id


@pytest.mark.asyncio
async def test_filter_todos_by_status_and_keyword(client: AsyncClient):
    user = await register(client, "filter-status@example.com")
    headers = auth_header(user["access_token"])

    done = await client.post("/api/v1/todos", json={"title": "Buy milk"}, headers=headers)
    await client.put(f"/api/v1/todos/{done.json()['id']}", json={"completed": True}, headers=headers)
    await client.post("/api/v1/todos", json={"title": "Buy eggs"}, headers=headers)

    active_resp = await client.get("/api/v1/todos?status=active", headers=headers)
    assert all(item["completed"] is False for item in active_resp.json()["items"])

    keyword_resp = await client.get("/api/v1/todos?keyword=milk", headers=headers)
    titles = [item["title"] for item in keyword_resp.json()["items"]]
    assert titles == ["Buy milk"]


# ---------------------------------------------------------------------------
# Bulk update ownership check
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_bulk_update_only_affects_own_todos(client: AsyncClient):
    user_a = await register(client, "bulk-a@example.com")
    user_b = await register(client, "bulk-b@example.com")
    headers_a = auth_header(user_a["access_token"])
    headers_b = auth_header(user_b["access_token"])

    a1 = (await client.post("/api/v1/todos", json={"title": "A1"}, headers=headers_a)).json()
    a2 = (await client.post("/api/v1/todos", json={"title": "A2"}, headers=headers_a)).json()
    b1 = (await client.post("/api/v1/todos", json={"title": "B1"}, headers=headers_b)).json()

    # A attempts to bulk-complete its own 2 todos AND B's todo.
    response = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [a1["id"], a2["id"], b1["id"]], "completed": True},
        headers=headers_a,
    )

    assert response.status_code == 200
    data = response.json()
    assert sorted(data["updated_ids"]) == sorted([a1["id"], a2["id"]])
    assert data["skipped_ids"] == [b1["id"]]

    # B's todo must be untouched.
    b1_check = await client.get(f"/api/v1/todos/{b1['id']}", headers=headers_b)
    assert b1_check.json()["completed"] is False


# ---------------------------------------------------------------------------
# Cache invalidation (tags/bulk)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_invalidated_on_tag_attach(client: AsyncClient):
    user = await register(client, "cache-tag-attach@example.com")
    headers = auth_header(user["access_token"])

    todo = (await client.post("/api/v1/todos", json={"title": "T"}, headers=headers)).json()
    tag = (await client.post("/api/v1/tags", json={"name": "X"}, headers=headers)).json()

    primed = await client.get("/api/v1/todos", headers=headers)
    assert primed.json()["items"][0]["tags"] == []
    assert any(k.startswith("todos:list:") for k in fake_redis.store)

    await client.post(f"/api/v1/todos/{todo['id']}/tags", json={"tag_id": tag["id"]}, headers=headers)

    refreshed = await client.get("/api/v1/todos", headers=headers)
    assert [t["id"] for t in refreshed.json()["items"][0]["tags"]] == [tag["id"]]


@pytest.mark.asyncio
async def test_cache_invalidated_on_bulk_update(client: AsyncClient):
    user = await register(client, "cache-bulk@example.com")
    headers = auth_header(user["access_token"])

    todo = (await client.post("/api/v1/todos", json={"title": "T"}, headers=headers)).json()

    primed = await client.get("/api/v1/todos?status=active", headers=headers)
    assert primed.json()["total"] == 1

    await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [todo["id"]], "completed": True},
        headers=headers,
    )

    refreshed = await client.get("/api/v1/todos?status=active", headers=headers)
    assert refreshed.json()["total"] == 0, "stale cached 'active' list served after bulk update"
