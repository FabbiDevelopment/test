import asyncio
import uuid

import pytest
from sqlalchemy import select

from app.api.v1.todos import todo_cache_version_key
from app.core.redis import redis_client
from app.core.security import verify_token
from app.db.session import async_session_maker
from app.models.todo import Todo

pytestmark = pytest.mark.integration


async def test_real_postgresql_and_redis_isolate_and_invalidate_todo_lists(
    integration_context,
):
    tokens_a, headers_a = await integration_context.register_user()
    tokens_b, headers_b = await integration_context.register_user()

    created_a = await integration_context.client.post(
        "/api/v1/todos",
        headers=headers_a,
        json={"title": "Private Todo A"},
    )
    created_b = await integration_context.client.post(
        "/api/v1/todos",
        headers=headers_b,
        json={"title": "Private Todo B"},
    )
    assert created_a.status_code == 201, created_a.text
    assert created_b.status_code == 201, created_b.text

    access_payload = verify_token(tokens_a["access_token"])
    assert access_payload is not None
    user_a_id = uuid.UUID(access_payload["sub"])
    tokens_b_payload = verify_token(tokens_b["access_token"])
    assert tokens_b_payload is not None
    user_b_id = uuid.UUID(tokens_b_payload["sub"])

    first_list_a = await integration_context.client.get(
        "/api/v1/todos?page=1&size=20", headers=headers_a
    )
    first_list_b = await integration_context.client.get(
        "/api/v1/todos?page=1&size=20", headers=headers_b
    )
    assert first_list_a.status_code == 200
    assert first_list_b.status_code == 200
    assert [todo["title"] for todo in first_list_a.json()["items"]] == [
        "Private Todo A"
    ]
    assert [todo["title"] for todo in first_list_b.json()["items"]] == [
        "Private Todo B"
    ]
    cache_keys_a = {
        key
        async for key in redis_client.client.scan_iter(
            match=f"todos:list:{user_a_id}:v*:page=1:size=20:*"
        )
    }
    cache_keys_b = {
        key
        async for key in redis_client.client.scan_iter(
            match=f"todos:list:{user_b_id}:v*:page=1:size=20:*"
        )
    }
    assert cache_keys_a
    assert cache_keys_b
    assert cache_keys_a.isdisjoint(cache_keys_b)

    cache_version_before = await redis_client.get(todo_cache_version_key(user_a_id))
    updated = await integration_context.client.put(
        f"/api/v1/todos/{created_a.json()['id']}",
        headers=headers_a,
        json={"title": "Updated Todo A"},
    )
    assert updated.status_code == 200, updated.text
    assert await redis_client.get(todo_cache_version_key(user_a_id)) == str(
        int(cache_version_before or "0") + 1
    )

    fresh_list_a = await integration_context.client.get(
        "/api/v1/todos?page=1&size=20", headers=headers_a
    )
    assert [todo["title"] for todo in fresh_list_a.json()["items"]] == [
        "Updated Todo A"
    ]

    async with async_session_maker() as session:
        persisted_todo = await session.scalar(
            select(Todo).where(Todo.id == created_a.json()["id"])
        )
    assert persisted_todo is not None
    assert persisted_todo.title == "Updated Todo A"


async def test_real_redis_allows_only_one_concurrent_refresh(integration_context):
    tokens, _ = await integration_context.register_user()
    refresh_request = {"refresh_token": tokens["refresh_token"]}

    responses = await asyncio.gather(
        *[
            integration_context.client.post(
                "/api/v1/auth/refresh", json=refresh_request
            )
            for _ in range(2)
        ]
    )

    assert sorted(response.status_code for response in responses) == [200, 401]
    successful_response = next(
        response for response in responses if response.status_code == 200
    )
    integration_context.track_token_pair(successful_response.json())

    rotated_refresh = await integration_context.client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": successful_response.json()["refresh_token"]},
    )
    assert rotated_refresh.status_code == 200, rotated_refresh.text
    integration_context.track_token_pair(rotated_refresh.json())


async def test_real_redis_invalidates_todo_lists_for_tag_mapping_and_bulk_mutations(
    integration_context,
):
    """Tier 4 mutations must advance the real owner-scoped Todo cache version."""
    tokens, headers = await integration_context.register_user()
    payload = verify_token(tokens["access_token"])
    assert payload is not None
    user_id = uuid.UUID(payload["sub"])

    created_todo = await integration_context.client.post(
        "/api/v1/todos",
        headers=headers,
        json={"title": "Real Redis Tag Todo"},
    )
    assert created_todo.status_code == 201, created_todo.text
    initial_list = await integration_context.client.get(
        "/api/v1/todos", headers=headers
    )
    assert initial_list.status_code == 200
    version = int(await redis_client.get(todo_cache_version_key(user_id)) or "0")

    created_tag = await integration_context.client.post(
        "/api/v1/tags",
        headers=headers,
        json={"name": "Real Redis Tag"},
    )
    assert created_tag.status_code == 201, created_tag.text
    version += 1
    assert await redis_client.get(todo_cache_version_key(user_id)) == str(version)

    attached = await integration_context.client.post(
        f"/api/v1/todos/{created_todo.json()['id']}/tags",
        headers=headers,
        json={"tag_id": created_tag.json()["id"]},
    )
    assert attached.status_code == 204, attached.text
    version += 1
    assert await redis_client.get(todo_cache_version_key(user_id)) == str(version)

    bulk_updated = await integration_context.client.patch(
        "/api/v1/todos/bulk-status",
        headers=headers,
        json={"todo_ids": [created_todo.json()["id"]], "completed": True},
    )
    assert bulk_updated.status_code == 200, bulk_updated.text
    version += 1
    assert await redis_client.get(todo_cache_version_key(user_id)) == str(version)

    deleted_tag = await integration_context.client.delete(
        f"/api/v1/tags/{created_tag.json()['id']}",
        headers=headers,
    )
    assert deleted_tag.status_code == 204, deleted_tag.text
    version += 1
    assert await redis_client.get(todo_cache_version_key(user_id)) == str(version)
