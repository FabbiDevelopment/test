"""Todo tests."""

import pytest
from httpx import AsyncClient


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
async def test_partial_update_preserves_description_and_can_mark_active(client: AsyncClient):
    token = await get_auth_token(client, "partial-update@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    created = await client.post(
        "/api/v1/todos",
        json={"title": "Original", "description": "Keep this"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    await client.put(f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers)
    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Renamed", "completed": False},
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False
    assert response.json()["description"] == "Keep this"


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
async def test_user_cannot_read_another_users_todo(client: AsyncClient):
    """Users must not access todos owned by another user."""
    owner_token = await get_auth_token(client, "owner@example.com")
    other_user_token = await get_auth_token(client, "other@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Private Todo"},
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    todo_id = create_response.json()["id"]

    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {other_user_token}"},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("method", ["put", "delete"])
async def test_user_cannot_modify_another_users_todo(client: AsyncClient, method):
    owner = {
        "Authorization": f"Bearer {await get_auth_token(client, 'owner@example.com')}"
    }
    other = {
        "Authorization": f"Bearer {await get_auth_token(client, 'other@example.com')}"
    }
    created = await client.post(
        "/api/v1/todos", headers=owner, json={"title": "Private"}
    )
    url = f"/api/v1/todos/{created.json()['id']}"
    kwargs = {"json": {"title": "Stolen"}} if method == "put" else {}
    response = await client.request(method, url, headers=other, **kwargs)
    assert response.status_code == 404
    assert (await client.get(url, headers=owner)).json()["title"] == "Private"


async def test_cached_lists_are_isolated_by_user_and_pagination(client, redis_cache):
    owner = {
        "Authorization": f"Bearer {await get_auth_token(client, 'owner@example.com')}"
    }
    other = {
        "Authorization": f"Bearer {await get_auth_token(client, 'other@example.com')}"
    }
    for title in ("First", "Second"):
        assert (
            await client.post("/api/v1/todos", headers=owner, json={"title": title})
        ).status_code == 201
    first = (await client.get("/api/v1/todos?page=1&size=1", headers=owner)).json()
    writes = redis_cache.set.await_count
    assert (
        await client.get("/api/v1/todos?page=1&size=1", headers=owner)
    ).json() == first
    assert redis_cache.set.await_count == writes
    second = (await client.get("/api/v1/todos?page=2&size=1", headers=owner)).json()
    assert first["items"][0]["id"] != second["items"][0]["id"]
    assert (
        len(
            (await client.get("/api/v1/todos?page=1&size=2", headers=owner)).json()[
                "items"
            ]
        )
        == 2
    )
    assert (await client.get("/api/v1/todos?page=1&size=1", headers=other)).json()[
        "items"
    ] == []


async def test_mutations_invalidate_all_cached_pages_after_commit(client, redis_cache):
    from sqlalchemy import select
    from app.models.todo import Todo
    from tests.conftest import test_session_maker

    auth = {"Authorization": f"Bearer {await get_auth_token(client)}"}
    url = "/api/v1/todos"
    observed_titles = []
    original_set = redis_cache.set.side_effect

    async def observe_committed_data(key, value, ex=None):
        if key.endswith(":version"):
            async with test_session_maker() as session:
                observed_titles.append(
                    list((await session.scalars(select(Todo.title))).all())
                )
        await original_set(key, value, ex)

    redis_cache.set.side_effect = observe_committed_data
    for size in (1, 2):
        assert (await client.get(url, params={"size": size}, headers=auth)).json()[
            "total"
        ] == 0
    created = (await client.post(url, headers=auth, json={"title": "Original"})).json()
    item_url = f"{url}/{created['id']}"
    for size in (1, 2):
        assert (await client.get(url, params={"size": size}, headers=auth)).json()[
            "total"
        ] == 1
    assert (
        await client.put(item_url, headers=auth, json={"title": "Updated"})
    ).status_code == 200
    for size in (1, 2):
        assert (await client.get(url, params={"size": size}, headers=auth)).json()[
            "items"
        ][0]["title"] == "Updated"
    assert (await client.delete(item_url, headers=auth)).status_code == 204
    for size in (1, 2):
        assert (await client.get(url, params={"size": size}, headers=auth)).json()[
            "total"
        ] == 0
    assert observed_titles == [["Original"], ["Updated"], []]
