"""
Cache invalidation tests — Kiểm thử vô hiệu hóa Redis cache sau mutation.
Verifies create/update/delete clears stale cached todo lists.
"""

import json

import pytest
from httpx import AsyncClient

from tests.conftest import MockRedisClient, register_and_get_token


@pytest.mark.asyncio
async def test_create_invalidates_todo_list_cache(
    client: AsyncClient, redis_store: MockRedisClient
):
    """
    THÊM: POST /todos phải invalidate cache — tránh trả về danh sách cũ thiếu item mới.
    SAI (bug cũ): create không gọi redis delete → stale data tới hết TTL (300s).
    """
    token = await register_and_get_token(client, "cache-create@example.com")

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]
    # THÊM: key có filter hash — Level 4 cache format todos:list:{user}:{page}:{size}:{hash}
    cache_key = f"todos:list:{user_id}:1:20:deadbeef"

    stale_payload = {"items": [], "total": 0, "page": 1, "size": 20}
    redis_store._store[cache_key] = json.dumps(stale_payload)

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Fresh Todo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 201
    # delete_by_prefix — mọi key user bị xóa
    remaining = [k for k in redis_store._store if k.startswith(f"todos:list:{user_id}:")]
    assert len(remaining) == 0

    list_response = await client.get(
        "/api/v1/todos",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert list_response.status_code == 200
    assert any(item["title"] == "Fresh Todo" for item in list_response.json()["items"])


@pytest.mark.asyncio
async def test_update_invalidates_todo_list_cache(
    client: AsyncClient, redis_store: MockRedisClient
):
    """THÊM: PUT /todos/{id} phải invalidate cache sau update."""
    token = await register_and_get_token(client, "cache-update@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "Before Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]
    cache_key = f"todos:list:{user_id}:1:20:deadbeef"
    redis_store._store[cache_key] = json.dumps({"items": [], "total": 0, "page": 1, "size": 20})

    update_response = await client.put(
        f"/api/v1/todos/{todo_id}",
        json={"title": "After Update"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert update_response.status_code == 200
    remaining = [k for k in redis_store._store if k.startswith(f"todos:list:{user_id}:")]
    assert len(remaining) == 0


@pytest.mark.asyncio
async def test_delete_invalidates_todo_list_cache(
    client: AsyncClient, redis_store: MockRedisClient
):
    """THÊM: DELETE /todos/{id} phải invalidate cache sau delete."""
    token = await register_and_get_token(client, "cache-delete@example.com")

    create_response = await client.post(
        "/api/v1/todos",
        json={"title": "To Delete"},
        headers={"Authorization": f"Bearer {token}"},
    )
    todo_id = create_response.json()["id"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    user_id = me.json()["id"]
    cache_key = f"todos:list:{user_id}:1:20:deadbeef"
    redis_store._store[cache_key] = json.dumps({"items": [], "total": 0, "page": 1, "size": 20})

    delete_response = await client.delete(
        f"/api/v1/todos/{todo_id}",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert delete_response.status_code == 204
    remaining = [k for k in redis_store._store if k.startswith(f"todos:list:{user_id}:")]
    assert len(remaining) == 0
