"""Todo tests."""

from fnmatch import fnmatch

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


class FakeRedis:
    def __init__(self):
        self.values = {}
        self.set_calls = []
        self.deleted_keys = []
        self.deleted_patterns = []

    async def get(self, key: str):
        return self.values.get(key)

    async def set(self, key: str, value: str, ex: int | None = None):
        self.values[key] = value
        self.set_calls.append((key, value, ex))

    async def delete(self, key: str):
        self.deleted_keys.append(key)
        self.values.pop(key, None)

    async def delete_pattern(self, pattern: str):
        self.deleted_patterns.append(pattern)
        keys = [key for key in self.values if fnmatch(key, pattern)]
        for key in keys:
            await self.delete(key)


@pytest.fixture
def fake_redis():
    redis = FakeRedis()
    previous_override = app.dependency_overrides.get(get_redis)
    app.dependency_overrides[get_redis] = lambda: redis
    yield redis
    if previous_override is None:
        app.dependency_overrides.pop(get_redis, None)
    else:
        app.dependency_overrides[get_redis] = previous_override


@pytest.mark.asyncio
async def test_single_todo_routes_are_scoped_to_owner(client: AsyncClient):
    """Users cannot read, update, or delete another user's todo by UUID."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_token = await get_auth_token(client, "other@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private Todo"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    todo_id = create_response.json()["id"]

    get_response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Stolen"},
        headers={"Authorization": f"Bearer {other_token}"},
    )
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {other_token}"},
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404
    assert delete_response.status_code == 404


@pytest.mark.asyncio
async def test_todo_list_cache_is_scoped_by_user_and_pagination(
    client: AsyncClient, fake_redis: FakeRedis
):
    """Todo list cache keys include user id, page, and size."""
    first_token = await get_auth_token(client, "cache-one@example.com")
    second_token = await get_auth_token(client, "cache-two@example.com")

    await client.get(
        "/api/v1/todos?page=1&size=1",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    await client.get(
        "/api/v1/todos?page=2&size=1",
        headers={"Authorization": f"Bearer {first_token}"},
    )
    await client.get(
        "/api/v1/todos?page=1&size=1",
        headers={"Authorization": f"Bearer {second_token}"},
    )

    keys = [call[0] for call in fake_redis.set_calls]
    assert len(keys) == 3
    assert len(set(keys)) == 3
    assert all(key.startswith("todos:list:") for key in keys)
    assert all(":page:" in key and ":size:" in key for key in keys)


@pytest.mark.asyncio
async def test_todo_mutations_invalidate_current_users_list_cache(
    client: AsyncClient, fake_redis: FakeRedis
):
    """Create, update, and delete invalidate the mutating user's cached lists."""
    token = await get_auth_token(client, "invalidate@example.com")

    await client.get(
        "/api/v1/todos?page=1&size=20",
        headers={"Authorization": f"Bearer {token}"},
    )
    cache_key = fake_redis.set_calls[-1][0]

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Invalidate Me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]
    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert create_response.status_code == 201
    assert update_response.status_code == 200
    assert delete_response.status_code == 204
    expected_pattern = cache_key.rsplit(":page:", 1)[0] + ":*"
    assert fake_redis.deleted_patterns.count(expected_pattern) == 3
    assert cache_key in fake_redis.deleted_keys


@pytest.mark.asyncio
async def test_update_supports_completed_false_and_preserves_omitted_description(
    client: AsyncClient,
):
    """Partial updates use only provided fields, including completed=false."""
    token = await get_auth_token(client, "partial-update@example.com")
    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Partial", "description": "Keep me"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": True},
        headers={"Authorization": f"Bearer {token}"},
    )
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"completed": False},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["completed"] is False
    assert data["description"] == "Keep me"
