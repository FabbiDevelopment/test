"""Todo tests."""

import logging
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient
from redis.exceptions import RedisError
from sqlalchemy import inspect as sa_inspect
from sqlalchemy.exc import SQLAlchemyError

from app.api.v1.todos import commit_todo_mutation
from app.services.todo_service import get_todos


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_todo(client: AsyncClient):
    """Test creating a new todo."""
    token = await get_auth_token(client, "create@example.com")

    response = await client.post(
        "/api/v1/todos",
        json={"title": "Test Todo", "description": "A test todo item"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "A test todo item"
    assert data["completed"] is False


@pytest.mark.asyncio(loop_scope="session")
async def test_get_todos(client: AsyncClient):
    """Test getting todo list."""
    token = await get_auth_token(client, "list@example.com")

    # Create a todo first
    await client.post(
        "/api/v1/todos",
        json={"title": "List Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )

    # Get todos
    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_list_rejects_page_size_above_maximum(client: AsyncClient):
    """API-001: list requests cannot bypass the bounded page-size contract."""
    token = await get_auth_token(client, "page-size-limit@example.com")

    response = await client.get(
        "/api/v1/todos",
        params={"size": 101},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_get_todos_orders_newest_first(client: AsyncClient):
    """Pagination must have a stable newest-first order."""
    token = await get_auth_token(client, "ordered-list@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        "/api/v1/todos",
        json={"title": "Older todo"},
        headers=headers,
    )
    second = await client.post(
        "/api/v1/todos",
        json={"title": "Newer todo"},
        headers=headers,
    )
    response = await client.get("/api/v1/todos", headers=headers)

    assert response.status_code == 200
    assert [item["id"] for item in response.json()["items"]] == [
        second.json()["id"],
        first.json()["id"],
    ]


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_list_eager_loads_users_for_response(
    client: AsyncClient,
    db_session,
):
    """DB-003: list queries load Todo users without one query per Todo."""
    token = await get_auth_token(client, "eager-users@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = []
    for title in ("First todo", "Second todo"):
        response = await client.post(
            "/api/v1/todos",
            json={"title": title},
            headers=headers,
        )
        created.append(response.json())

    todos, total = await get_todos(
        db_session,
        user_id=uuid.UUID(created[0]["user_id"]),
    )

    assert total == 2
    assert all("user" not in sa_inspect(todo).unloaded for todo in todos)


@pytest.mark.asyncio(loop_scope="session")
async def test_update_todo(client: AsyncClient):
    """Test updating a todo."""
    token = await get_auth_token(client, "update@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Update Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Update it
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated Title", "completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"


@pytest.mark.asyncio(loop_scope="session")
async def test_delete_todo(client: AsyncClient):
    """Test deleting a todo."""
    token = await get_auth_token(client, "delete@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Delete Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Delete it
    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 204


@pytest.mark.asyncio(loop_scope="session")
async def test_get_single_todo(client: AsyncClient):
    """Test getting a single todo by ID."""
    token = await get_auth_token(client, "single@example.com")

    # Create a todo
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Single Todo", "description": "Get me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    # Get it
    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Single Todo"


@pytest.mark.asyncio(loop_scope="session")
@pytest.mark.parametrize("method", ["get", "put", "delete"])
async def test_user_cannot_access_another_users_todo(
    client: AsyncClient,
    method: str,
):
    """TODO-001: detail reads and mutations must be scoped to the owner."""
    owner_token = await get_auth_token(client, f"owner-{method}@example.com")
    attacker_token = await get_auth_token(client, f"attacker-{method}@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    attacker_headers = {"Authorization": f"Bearer {attacker_token}"}

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Owner private todo", "description": "Owner secret"},
        headers=owner_headers,
    )
    todo_id = created.json()["id"]

    if method == "put":
        attack_response = await client.put(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Changed by attacker", "completed": True},
            headers=attacker_headers,
        )
    else:
        attack_response = await client.request(
            method,
            f"/api/v1/todos/{todo_id}",
            headers=attacker_headers,
        )

    owner_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=owner_headers,
    )

    assert attack_response.status_code == 404
    assert owner_response.status_code == 200
    assert owner_response.json()["title"] == "Owner private todo"
    assert owner_response.json()["completed"] is False


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_cache_is_isolated_by_user(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """CACHE-001: one user's cached list must never be served to another user."""
    user_a_token = await get_auth_token(client, "cache-user-a@example.com")
    user_b_token = await get_auth_token(client, "cache-user-b@example.com")
    user_a_headers = {"Authorization": f"Bearer {user_a_token}"}
    user_b_headers = {"Authorization": f"Bearer {user_b_token}"}

    await client.post(
        "/api/v1/todos",
        json={"title": "User A private todo"},
        headers=user_a_headers,
    )
    await client.post(
        "/api/v1/todos",
        json={"title": "User B private todo"},
        headers=user_b_headers,
    )

    user_a_response = await client.get("/api/v1/todos", headers=user_a_headers)
    user_b_response = await client.get("/api/v1/todos", headers=user_b_headers)

    assert user_a_response.status_code == 200
    assert user_b_response.status_code == 200
    assert [item["title"] for item in user_a_response.json()["items"]] == [
        "User A private todo"
    ]
    assert [item["title"] for item in user_b_response.json()["items"]] == [
        "User B private todo"
    ]


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_cache_is_isolated_by_pagination_query(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """CACHE-001: pagination inputs must be part of the list cache identity."""
    token = await get_auth_token(client, "cache-query@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    for title in ("First todo", "Second todo"):
        await client.post(
            "/api/v1/todos",
            json={"title": title},
            headers=headers,
        )

    first_page = await client.get(
        "/api/v1/todos",
        params={"page": 1, "size": 1},
        headers=headers,
    )
    second_page = await client.get(
        "/api/v1/todos",
        params={"page": 2, "size": 1},
        headers=headers,
    )

    assert first_page.status_code == 200
    assert second_page.status_code == 200
    assert first_page.json()["page"] == 1
    assert second_page.json()["page"] == 2
    assert first_page.json()["items"][0]["id"] != second_page.json()["items"][0]["id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_mutations_invalidate_cached_lists(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """CACHE-002: create, update, and delete must not serve stale lists."""
    token = await get_auth_token(client, "cache-invalidation@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    first = await client.post(
        "/api/v1/todos",
        json={"title": "First todo"},
        headers=headers,
    )
    await client.post(
        "/api/v1/todos",
        json={"title": "Second todo"},
        headers=headers,
    )
    first_id = first.json()["id"]

    await client.get("/api/v1/todos", headers=headers)
    await client.get(
        "/api/v1/todos",
        params={"page": 2, "size": 1},
        headers=headers,
    )

    await client.post(
        "/api/v1/todos",
        json={"title": "Third todo"},
        headers=headers,
    )
    after_create = await client.get("/api/v1/todos", headers=headers)
    second_page_after_create = await client.get(
        "/api/v1/todos",
        params={"page": 2, "size": 1},
        headers=headers,
    )

    assert after_create.json()["total"] == 3
    assert second_page_after_create.json()["total"] == 3

    await client.put(
        f"/api/v1/todos/{first_id}",
        json={"title": "Updated first todo"},
        headers=headers,
    )
    after_update = await client.get("/api/v1/todos", headers=headers)

    assert {item["title"] for item in after_update.json()["items"]} == {
        "Updated first todo",
        "Second todo",
        "Third todo",
    }

    await client.delete(f"/api/v1/todos/{first_id}", headers=headers)
    after_delete = await client.get("/api/v1/todos", headers=headers)

    assert after_delete.json()["total"] == 2
    assert {item["title"] for item in after_delete.json()["items"]} == {
        "Second todo",
        "Third todo",
    }


@pytest.mark.asyncio(loop_scope="session")
async def test_failed_todo_commit_does_not_invalidate_cache():
    """CACHE-003: Redis version changes only after a successful DB commit."""
    db = MagicMock()
    db.commit = AsyncMock(side_effect=SQLAlchemyError("commit failed"))
    db.rollback = AsyncMock()
    redis = MagicMock()
    redis.incr = AsyncMock()
    user_id = "00000000-0000-0000-0000-000000000001"

    with pytest.raises(SQLAlchemyError, match="commit failed"):
        await commit_todo_mutation(db, redis, user_id)

    db.rollback.assert_awaited_once()
    redis.incr.assert_not_awaited()


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_cache_invalidation_follows_successful_commit():
    """CACHE-003: cache version changes only after the transaction commits."""
    events: list[str] = []
    db = MagicMock()
    db.commit = AsyncMock(side_effect=lambda: events.append("commit"))
    redis = MagicMock()
    redis.incr = AsyncMock(side_effect=lambda _: events.append("invalidate"))

    await commit_todo_mutation(
        db,
        redis,
        uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )

    assert events == ["commit", "invalidate"]


@pytest.mark.asyncio(loop_scope="session")
async def test_create_todo_succeeds_when_cache_invalidation_is_unavailable(
    client: AsyncClient,
    shared_redis: MagicMock,
    caplog: pytest.LogCaptureFixture,
):
    """CACHE-004: a committed Todo must not become a 500 when Redis is down."""
    token = await get_auth_token(client, "redis-outage@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    shared_redis.incr.side_effect = RedisError("Redis unavailable")
    caplog.set_level(logging.WARNING, logger="app.services.todo_cache_service")

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Persist despite cache outage"},
        headers=headers,
    )
    listed = await client.get("/api/v1/todos", headers=headers)

    assert created.status_code == 201
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()["items"]] == [created.json()["id"]]
    assert "todo_cache_invalidation_failed" in caplog.text


@pytest.mark.asyncio(loop_scope="session")
async def test_partial_update_can_set_completed_to_false(client: AsyncClient):
    """TODO-002: explicit false must be persisted instead of treated as omitted."""
    token = await get_auth_token(client, "completed-false@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle me"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    completed = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers=headers,
    )
    reopened = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers=headers,
    )
    persisted = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
    )

    assert completed.status_code == 200
    assert completed.json()["completed"] is True
    assert reopened.status_code == 200
    assert reopened.json()["completed"] is False
    assert persisted.json()["completed"] is False


@pytest.mark.asyncio(loop_scope="session")
async def test_partial_update_preserves_omitted_description(client: AsyncClient):
    """TODO-003: omitted fields must retain their stored values."""
    token = await get_auth_token(client, "preserve-description@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Original title", "description": "Keep this description"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    updated = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Updated title"},
        headers=headers,
    )
    persisted = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers=headers,
    )

    assert updated.status_code == 200
    assert updated.json()["description"] == "Keep this description"
    assert persisted.json()["description"] == "Keep this description"
