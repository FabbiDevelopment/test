"""Regression tests for the todo partial-update endpoint."""

import pytest
from httpx import AsyncClient

from tests.test_todos import get_auth_token


@pytest.mark.asyncio
async def test_toggle_completed_false_persists(client: AsyncClient):
    token = await get_auth_token(client, "toggle-false@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Toggle target", "description": "Keep me"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    turned_off = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": False}, headers=headers
    )

    assert turned_off.status_code == 200
    assert turned_off.json()["completed"] is False


@pytest.mark.asyncio
async def test_partial_update_preserves_description(client: AsyncClient):
    token = await get_auth_token(client, "partial-update@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos",
        json={"title": "Has description", "description": "Do not erase me"},
        headers=headers,
    )
    todo_id = created.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["description"] == "Do not erase me"


@pytest.mark.asyncio
async def test_explicit_null_completed_does_not_500(client: AsyncClient):
    token = await get_auth_token(client, "null-completed@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos", json={"title": "Null completed"}, headers=headers
    )
    todo_id = created.json()["id"]

    response = await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": None}, headers=headers
    )

    assert response.status_code == 200
    assert response.json()["completed"] is False
