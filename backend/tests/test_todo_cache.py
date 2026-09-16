"""Regression tests for the per-user todo list cache."""

import pytest
from httpx import AsyncClient

from tests.test_todos import get_auth_token


@pytest.mark.asyncio
async def test_new_todo_appears_after_cached_list(client: AsyncClient, redis_fake):
    token = await get_auth_token(client, "cache-create@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/todos", json={"title": "First"}, headers=headers)
    first_list = await client.get("/api/v1/todos", headers=headers)
    assert len(first_list.json()["items"]) == 1

    await client.post("/api/v1/todos", json={"title": "Second"}, headers=headers)
    second_list = await client.get("/api/v1/todos", headers=headers)
    assert len(second_list.json()["items"]) == 2


@pytest.mark.asyncio
async def test_toggle_is_reflected_after_cached_list(client: AsyncClient, redis_fake):
    token = await get_auth_token(client, "cache-toggle@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/todos", json={"title": "Toggle me"}, headers=headers
    )
    todo_id = created.json()["id"]

    await client.get("/api/v1/todos", headers=headers)  # warms the cache

    await client.put(
        f"/api/v1/todos/{todo_id}", json={"completed": True}, headers=headers
    )
    after_toggle = await client.get("/api/v1/todos", headers=headers)
    assert after_toggle.json()["items"][0]["completed"] is True


@pytest.mark.asyncio
async def test_list_cache_is_scoped_per_user(client: AsyncClient, redis_fake):
    token_a = await get_auth_token(client, "cache-user-a@example.com")
    token_b = await get_auth_token(client, "cache-user-b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    await client.post("/api/v1/todos", json={"title": "A only"}, headers=headers_a)
    await client.get("/api/v1/todos", headers=headers_a)  # warms A's cache entry

    b_list = await client.get("/api/v1/todos", headers=headers_b)
    assert b_list.json()["items"] == []
