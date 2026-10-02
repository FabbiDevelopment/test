"""Todo tests."""

import uuid
from fnmatch import fnmatchcase
from unittest.mock import AsyncMock, MagicMock

import pytest
from httpx import AsyncClient

from app.api.deps import get_redis
from app.main import app


async def get_auth_token(client: AsyncClient, email: str = "todo@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_toggle_todo_completion_both_directions(client: AsyncClient):
    """Both boolean values persist, including unchecking a completed todo."""
    token = await get_auth_token(client, "toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle me", "description": "Keep these details"},
        headers=headers,
    )
    assert created.status_code == 201
    url = f"/api/v1/todos/{created.json()['id']}"

    for completed in (True, False, True, False):
        updated = await client.put(url, json={"completed": completed}, headers=headers)
        assert updated.status_code == 200
        persisted = await client.get(url, headers=headers)
        listed = await client.get("/api/v1/todos", headers=headers)
        assert persisted.status_code == 200
        assert listed.status_code == 200
        for data in (updated.json(), persisted.json(), listed.json()["items"][0]):
            assert data["completed"] is completed
            assert data["title"] == "Toggle me"
            assert data["description"] == "Keep these details"


@pytest.mark.asyncio
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


@pytest.mark.asyncio
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


@pytest.mark.asyncio
async def test_mutations_invalidate_todo_list_cache(client: AsyncClient):
    """Creating, updating, and deleting todos invalidate the cached list."""
    redis = MagicMock()
    redis.delete_pattern = AsyncMock()
    previous_override = app.dependency_overrides[get_redis]
    app.dependency_overrides[get_redis] = lambda: redis

    try:
        token = await get_auth_token(client, "cache@example.com")
        headers = {"Authorization": f"Bearer {token}"}

        create_response = await client.post(
            "/api/v1/todos",
            json={"title": "Cache Me"},
            headers=headers,
        )
        assert create_response.status_code == 201
        todo_id = create_response.json()["id"]

        update_response = await client.put(
            f"/api/v1/todos/{todo_id}",
            json={"title": "Updated Cache"},
            headers=headers,
        )
        assert update_response.status_code == 200
        delete_response = await client.delete(
            f"/api/v1/todos/{todo_id}", headers=headers
        )
        assert delete_response.status_code == 204
    finally:
        app.dependency_overrides[get_redis] = previous_override

    assert redis.delete_pattern.await_count == 3
    redis.delete_pattern.assert_called_with(
        f"todos:{create_response.json()['user_id']}:list:*"
    )


@pytest.mark.asyncio
async def test_list_cache_isolates_users_pages_and_invalidates_updates(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch
):
    """Cached lists cannot expose another user's todos or stale completion state."""
    cache_data: dict[str, str] = {}

    async def get_cache(key: str):
        return cache_data.get(key)

    async def set_cache(key: str, value: str, ex=None):
        cache_data[key] = value

    async def delete_cache(pattern: str):
        for key in list(cache_data):
            if fnmatchcase(key, pattern):
                cache_data.pop(key)

    redis = MagicMock()
    redis.get = AsyncMock(side_effect=get_cache)
    redis.set = AsyncMock(side_effect=set_cache)
    redis.delete_pattern = AsyncMock(side_effect=delete_cache)
    redis.delete = AsyncMock(side_effect=delete_cache)
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)

    token_a = await get_auth_token(client, "cache-a@example.com")
    token_b = await get_auth_token(client, "cache-b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}
    created_a = []
    for title in ("A first", "A second"):
        response = await client.post(
            "/api/v1/todos", json={"title": title}, headers=headers_a
        )
        assert response.status_code == 201
        created_a.append(response.json())
    response = await client.post(
        "/api/v1/todos", json={"title": "B private"}, headers=headers_b
    )
    assert response.status_code == 201
    created_b = response.json()

    for _ in range(2):  # Repeat to cover cache hits as well as cold reads.
        page_ids = set()
        for page in (1, 2):
            response = await client.get(
                "/api/v1/todos", params={"page": page, "size": 1}, headers=headers_a
            )
            assert response.status_code == 200
            data = response.json()
            assert data["page"] == page
            assert data["size"] == 1
            assert data["total"] == 2
            assert len(data["items"]) == 1
            page_ids.add(data["items"][0]["id"])
        assert page_ids == {todo["id"] for todo in created_a}
        response = await client.get(
            "/api/v1/todos", params={"size": 2}, headers=headers_a
        )
        assert {todo["id"] for todo in response.json()["items"]} == page_ids
        response = await client.get(
            "/api/v1/todos", params={"size": 2}, headers=headers_b
        )
        assert response.status_code == 200
        assert response.json()["total"] == 1
        assert [todo["id"] for todo in response.json()["items"]] == [created_b["id"]]

    denied = await client.put(
        f"/api/v1/todos/{created_a[0]['id']}",
        json={"completed": True},
        headers=headers_b,
    )
    assert denied.status_code == 404

    for completed in (True, False):
        response = await client.put(
            f"/api/v1/todos/{created_a[0]['id']}",
            json={"completed": completed},
            headers=headers_a,
        )
        assert response.status_code == 200
        assert response.json()["completed"] is completed
        # All cached sizes/pages for A were invalidated; B's cache stays intact.
        assert not any(
            key.startswith(f"todos:{created_a[0]['user_id']}:list:")
            for key in cache_data
        )
        assert any(
            key.startswith(f"todos:{created_b['user_id']}:list:") for key in cache_data
        )
        for page, size in ((1, 1), (2, 1), (1, 2)):
            response = await client.get(
                "/api/v1/todos", params={"page": page, "size": size}, headers=headers_a
            )
            assert response.status_code == 200
            for todo in response.json()["items"]:
                if todo["id"] == created_a[0]["id"]:
                    assert todo["completed"] is completed


@pytest.mark.asyncio
@pytest.mark.parametrize("operation", ["create", "update", "delete"])
async def test_mutation_is_committed_before_cache_refill(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, operation: str
):
    """A concurrent GET after invalidation must see the committed mutation."""
    token = await get_auth_token(client, f"cache-race-{operation}@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    cache_data: dict[str, str] = {}

    async def get_cache(key: str):
        return cache_data.get(key)

    async def set_cache(key: str, value: str, ex=None):
        cache_data[key] = value

    async def delete_cache(pattern: str):
        for key in list(cache_data):
            if fnmatchcase(key, pattern):
                cache_data.pop(key)

    redis = MagicMock()
    redis.get = AsyncMock(side_effect=get_cache)
    redis.set = AsyncMock(side_effect=set_cache)
    redis.delete_pattern = AsyncMock(side_effect=delete_cache)
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)

    created = await client.post(
        "/api/v1/todos", json={"title": "Original"}, headers=headers
    )
    assert created.status_code == 201
    todo_id = created.json()["id"]
    primed = await client.get("/api/v1/todos", headers=headers)
    assert primed.status_code == 200
    assert primed.json()["total"] == 1
    assert cache_data

    expected_titles = {
        "create": {"Original", "New"},
        "update": {"Updated"},
        "delete": set(),
    }[operation]

    async def invalidate_and_refill(key: str):
        await delete_cache(key)
        # This is a separate request/session while the mutation is still running.
        response = await client.get("/api/v1/todos", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == len(expected_titles)
        assert {item["title"] for item in data["items"]} == expected_titles

    redis.delete_pattern.side_effect = invalidate_and_refill
    if operation == "create":
        response = await client.post(
            "/api/v1/todos", json={"title": "New"}, headers=headers
        )
        assert response.status_code == 201
    elif operation == "update":
        response = await client.put(
            f"/api/v1/todos/{todo_id}", json={"title": "Updated"}, headers=headers
        )
        assert response.status_code == 200
    else:
        response = await client.delete(f"/api/v1/todos/{todo_id}", headers=headers)
        assert response.status_code == 204

    redis.delete_pattern.assert_awaited_with(
        f"todos:{created.json()['user_id']}:list:*"
    )
    cached = await client.get("/api/v1/todos", headers=headers)
    assert cached.status_code == 200
    assert {item["title"] for item in cached.json()["items"]} == expected_titles


@pytest.mark.asyncio
@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
async def test_todo_access_requires_ownership(
    client: AsyncClient, monkeypatch: pytest.MonkeyPatch, method: str
):
    """Other users cannot access or mutate a todo, while its owner still can."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Private todo", "description": "Private description"},
        headers=owner_headers,
    )
    assert created.status_code == 201
    original = created.json()
    url = f"/api/v1/todos/{original['id']}"

    redis = MagicMock()
    redis.delete_pattern = AsyncMock()
    monkeypatch.setitem(app.dependency_overrides, get_redis, lambda: redis)
    request_data = {"json": {"title": "Changed"}} if method == "PUT" else {}

    denied = await client.request(method, url, headers=other_headers, **request_data)
    assert denied.status_code == 404
    assert denied.json() == {"detail": "Todo not found"}
    missing = await client.request(
        method, f"/api/v1/todos/{uuid.uuid4()}", headers=other_headers, **request_data
    )
    assert missing.status_code == 404
    assert missing.json() == denied.json()
    redis.delete_pattern.assert_not_awaited()

    # An independent request confirms failed mutations left the owner's data intact.
    unchanged = await client.get(url, headers=owner_headers)
    assert unchanged.status_code == 200
    for field in ("id", "user_id", "title", "description", "completed", "updated_at"):
        assert unchanged.json()[field] == original[field]

    # The authorization check must still permit each operation for the owner.
    allowed = await client.request(method, url, headers=owner_headers, **request_data)
    assert allowed.status_code == (204 if method == "DELETE" else 200)
    if method == "PUT":
        persisted = await client.get(url, headers=owner_headers)
        assert persisted.status_code == 200
        assert persisted.json()["title"] == "Changed"
    elif method == "DELETE":
        deleted = await client.get(url, headers=owner_headers)
        assert deleted.status_code == 404


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "payload, expected_title, expected_description, expected_completed",
    [
        ({"title": "Renamed"}, "Renamed", "Keep this description", False),
        ({"completed": True}, "Original", "Keep this description", True),
        ({}, "Original", "Keep this description", False),
        ({"description": "New details"}, "Original", "New details", False),
        ({"description": None}, "Original", None, False),
        ({"description": ""}, "Original", "", False),
    ],
)
async def test_partial_update_preserves_description(
    client: AsyncClient,
    payload: dict,
    expected_title: str,
    expected_description: str | None,
    expected_completed: bool,
):
    """Omitting description preserves it; an explicit value updates or clears it."""
    token = await get_auth_token(client, "partial-update@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Original", "description": "Keep this description"},
        headers=headers,
    )
    assert created.status_code == 201
    url = f"/api/v1/todos/{created.json()['id']}"

    updated = await client.put(url, json=payload, headers=headers)
    assert updated.status_code == 200
    persisted = await client.get(url, headers=headers)
    assert persisted.status_code == 200
    for data in (updated.json(), persisted.json()):
        assert data["title"] == expected_title
        assert data["description"] == expected_description
        assert data["completed"] is expected_completed
