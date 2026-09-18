"""Tier 2A: critical-path regression tests.

Covers all 5 scenarios listed in the README (only 3 are required):
  1. Expired / tampered JWT access token rejection.
  2. Authorization boundary: User A cannot read/update/delete User B's todos.
  3. Boolean toggle: completed True -> False persists.
  4. Partial update: updating title does not erase description.
  5. Cache invalidation: create/update/delete removes stale Redis cache.
"""

from datetime import timedelta

import pytest
from httpx import AsyncClient
from jose import jwt

from app.core.config import settings
from app.core.security import create_access_token
from tests.conftest import fake_redis


async def register(client: AsyncClient, email: str, password: str = "password123") -> dict:
    """Register a user and return the parsed token response."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password},
    )
    assert response.status_code == 201, response.text
    return response.json()


def user_id_from_token(token: str) -> str:
    """Decode the 'sub' claim out of an access token we already trust."""
    payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    return payload["sub"]


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# 1. Expired / tampered JWT access token rejection
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_expired_access_token_is_rejected(client: AsyncClient):
    """A token whose exp claim is in the past must be rejected, not accepted."""
    user = await register(client, "expired@example.com")

    expired_token = create_access_token(
        data={"sub": user_id_from_token(user["access_token"])},
        expires_delta=timedelta(minutes=-5),
    )

    response = await client.get("/api/v1/todos", headers=auth_header(expired_token))

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tampered_access_token_is_rejected(client: AsyncClient):
    """A token re-signed with a different secret (or hand-edited) must fail."""
    user = await register(client, "tampered@example.com")

    forged_token = jwt.encode(
        {"sub": user_id_from_token(user["access_token"]), "type": "access"},
        "not-the-real-secret",
        algorithm=settings.JWT_ALGORITHM,
    )

    response = await client.get("/api/v1/todos", headers=auth_header(forged_token))

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_missing_token_is_rejected(client: AsyncClient):
    response = await client.get("/api/v1/todos")
    assert response.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 2. Authorization boundary: User A cannot touch User B's todos
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_user_cannot_read_other_users_todo(client: AsyncClient):
    user_a = await register(client, "owner-read@example.com")
    user_b = await register(client, "intruder-read@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "A's private todo"},
        headers=auth_header(user_a["access_token"]),
    )
    todo_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=auth_header(user_b["access_token"]),
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_todo(client: AsyncClient):
    user_a = await register(client, "owner-update@example.com")
    user_b = await register(client, "intruder-update@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "A's todo"},
        headers=auth_header(user_a["access_token"]),
    )
    todo_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hijacked by B"},
        headers=auth_header(user_b["access_token"]),
    )
    assert response.status_code == 404

    # The todo must be unchanged when its real owner reads it back.
    verify = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=auth_header(user_a["access_token"]),
    )
    assert verify.json()["title"] == "A's todo"


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_todo(client: AsyncClient):
    user_a = await register(client, "owner-delete@example.com")
    user_b = await register(client, "intruder-delete@example.com")

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "A's todo"},
        headers=auth_header(user_a["access_token"]),
    )
    todo_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers=auth_header(user_b["access_token"]),
    )
    assert response.status_code == 404

    # Still readable by the real owner -> was not actually deleted.
    verify = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=auth_header(user_a["access_token"]),
    )
    assert verify.status_code == 200


@pytest.mark.asyncio
async def test_user_list_does_not_include_other_users_todos(client: AsyncClient):
    user_a = await register(client, "owner-list@example.com")
    user_b = await register(client, "intruder-list@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "A's todo"},
        headers=auth_header(user_a["access_token"]),
    )

    response = await client.get("/api/v1/todos", headers=auth_header(user_b["access_token"]))
    titles = [item["title"] for item in response.json()["items"]]

    assert "A's todo" not in titles


# ---------------------------------------------------------------------------
# 3. Boolean toggle: completed True -> False persists
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_completed_toggle_false_persists(client: AsyncClient):
    user = await register(client, "toggle@example.com")
    headers = auth_header(user["access_token"])

    create_resp = await client.post(
        "/api/v1/todos", json={"title": "Toggle me"}, headers=headers
    )
    todo_id = create_resp.json()["id"]

    # true -> should persist
    r1 = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    assert r1.json()["completed"] is True

    # true -> false: this is the exact bug scenario (falsy check silently
    # dropped the update).
    r2 = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": False}, headers=headers
    )
    assert r2.json()["completed"] is False

    verify = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
    assert verify.json()["completed"] is False


# ---------------------------------------------------------------------------
# 4. Partial update: updating title does not erase description
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    user = await register(client, "partial@example.com")
    headers = auth_header(user["access_token"])

    create_resp = await client.post(
        "/api/v1/todos",
        json={"title": "Original title", "description": "Keep me"},
        headers=headers,
    )
    todo_id = create_resp.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "New title"},
        headers=headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New title"
    assert data["description"] == "Keep me"


# ---------------------------------------------------------------------------
# 5. Cache invalidation: create/update/delete removes stale Redis cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cache_invalidated_on_create(client: AsyncClient):
    user = await register(client, "cache-create@example.com")
    headers = auth_header(user["access_token"])

    # Prime the cache with an empty list.
    first = await client.get("/api/v1/todos", headers=headers)
    assert first.json()["total"] == 0
    assert any(k.startswith("todos:list:") for k in fake_redis.store)

    await client.post("/api/v1/todos", json={"title": "New"}, headers=headers)

    second = await client.get("/api/v1/todos", headers=headers)
    assert second.json()["total"] == 1, "stale cached list was served after create"


@pytest.mark.asyncio
async def test_cache_invalidated_on_update(client: AsyncClient):
    user = await register(client, "cache-update@example.com")
    headers = auth_header(user["access_token"])

    create_resp = await client.post(
        "/api/v1/todos", json={"title": "Before"}, headers=headers
    )
    todo_id = create_resp.json()["id"]

    # Prime the list cache.
    await client.get("/api/v1/todos", headers=headers)

    await client.put(
        f"/api/v1/todos/{todo_id}", json={"title": "After"}, headers=headers
    )

    second = await client.get("/api/v1/todos", headers=headers)
    titles = [item["title"] for item in second.json()["items"]]
    assert "After" in titles
    assert "Before" not in titles, "stale cached list was served after update"


@pytest.mark.asyncio
async def test_cache_invalidated_on_delete(client: AsyncClient):
    user = await register(client, "cache-delete@example.com")
    headers = auth_header(user["access_token"])

    create_resp = await client.post(
        "/api/v1/todos", json={"title": "Doomed"}, headers=headers
    )
    todo_id = create_resp.json()["id"]

    # Prime the list cache.
    primed = await client.get("/api/v1/todos", headers=headers)
    assert primed.json()["total"] == 1

    await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)

    second = await client.get("/api/v1/todos", headers=headers)
    assert second.json()["total"] == 0, "stale cached list was served after delete"
