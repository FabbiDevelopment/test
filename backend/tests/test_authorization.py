"""Authorization tests: cross-user todo access must be forbidden."""

import pytest
from httpx import AsyncClient

from tests.conftest import register_and_get_token


async def _create_todo_for_user(
    client: AsyncClient, email: str, title: str = "Private Todo"
) -> str:
    token = await register_and_get_token(client, email)
    response = await client.post(
        "/api/v1/todos",
        json={"title": title, "description": "Secret description"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 201
    return response.json()["id"]


@pytest.mark.asyncio
async def test_user_cannot_read_other_users_todo(client: AsyncClient):
    """User A must not read User B's todo by ID."""
    todo_id = await _create_todo_for_user(client, "userb-read@example.com")
    token_a = await register_and_get_token(client, "usera-read@example.com")

    response = await client.get(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_update_other_users_todo(client: AsyncClient):
    """User A must not update User B's todo."""
    todo_id = await _create_todo_for_user(client, "userb-update@example.com")
    token_a = await register_and_get_token(client, "usera-update@example.com")

    response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "Hacked Title"},
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_cannot_delete_other_users_todo(client: AsyncClient):
    """User A must not delete User B's todo."""
    todo_id = await _create_todo_for_user(client, "userb-delete@example.com")
    token_a = await register_and_get_token(client, "usera-delete@example.com")

    response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_user_list_excludes_other_users_todos(client: AsyncClient):
    """User A's todo list must not contain User B's todos."""
    await _create_todo_for_user(client, "userb-list@example.com", "User B Secret")
    token_a = await register_and_get_token(client, "usera-list@example.com")

    await client.post(
        "/api/v1/todos",
        json={"title": "User A Todo"},
        headers={"Authorization": f"Bearer {token_a}"},
    )

    response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token_a}"},
    )
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    assert "User B Secret" not in titles
    assert "User A Todo" in titles
