"""Database regressions for the Tag and Todo-to-Tag schema."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.exc import IntegrityError

from app.models.tag import Tag, todo_tags
from app.models.todo import Todo
from app.models.user import User
from app.services.todo_cache_service import todo_cache_version_key


async def get_auth_token(client: AsyncClient, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    assert response.status_code == 201, response.text
    return response.json()["access_token"]


async def create_todo(client: AsyncClient, headers: dict, title: str, **data) -> dict:
    response = await client.post(
        "/api/v1/todos",
        json={"title": title, **data},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


async def create_tag(client: AsyncClient, headers: dict, name: str, **data) -> dict:
    response = await client.post(
        "/api/v1/tags",
        json={"name": name, **data},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio(loop_scope="session")
async def test_tag_names_are_case_insensitively_unique_per_user(db_session):
    """A user cannot create two tags whose names differ only by casing."""
    owner = User(email="tag-owner@example.com", hashed_password="hash")
    other_user = User(email="tag-other@example.com", hashed_password="hash")
    db_session.add_all([owner, other_user])
    await db_session.commit()
    other_user_id = other_user.id

    db_session.add(Tag(user_id=owner.id, name="Work", color="#2563eb"))
    await db_session.commit()

    db_session.add(Tag(user_id=owner.id, name="work"))
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

    db_session.add(Tag(user_id=other_user_id, name="WORK"))
    await db_session.commit()


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_tag_mapping_rejects_duplicate_pairs(db_session):
    """The composite primary key allows a Tag to be applied only once per Todo."""
    user = User(email="mapping-owner@example.com", hashed_password="hash")
    todo = Todo(title="Tagged Todo", user=user)
    tag = Tag(user=user, name="Important")
    db_session.add_all([user, todo, tag])
    await db_session.commit()

    mapping = {"todo_id": todo.id, "tag_id": tag.id}
    await db_session.execute(todo_tags.insert().values(**mapping))
    await db_session.commit()

    with pytest.raises(IntegrityError):
        await db_session.execute(todo_tags.insert().values(**mapping))
        await db_session.commit()
    await db_session.rollback()


def test_tag_and_todo_filtering_indexes_are_declared():
    """Schema metadata must retain the indexes used by Tag and Todo queries."""
    tag_indexes = {index.name for index in Tag.__table__.indexes}
    mapping_indexes = {index.name for index in todo_tags.indexes}
    todo_indexes = {index.name for index in Todo.__table__.indexes}

    assert {"ix_tags_user_id", "uq_tags_user_id_lower_name"} <= tag_indexes
    assert {"ix_todo_tags_todo_id", "ix_todo_tags_tag_id"} <= mapping_indexes
    assert "ix_todos_user_id_completed_created_at_id" in todo_indexes


@pytest.mark.asyncio(loop_scope="session")
async def test_tag_crud_is_owner_scoped_and_invalidates_todo_cache(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """Tag CRUD is private to its owner and refreshes that user's Todo lists."""
    owner_token = await get_auth_token(client, "tag-api-owner@example.com")
    other_token = await get_auth_token(client, "tag-api-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    await create_todo(client, owner_headers, "Cache this Todo")
    await client.get("/api/v1/todos", headers=owner_headers)

    work = await create_tag(client, owner_headers, "Work", color="#2563eb")
    duplicate = await client.post(
        "/api/v1/tags",
        json={"name": "work"},
        headers=owner_headers,
    )
    owner_list = await client.get("/api/v1/tags", headers=owner_headers)
    other_list = await client.get("/api/v1/tags", headers=other_headers)

    assert duplicate.status_code == 409
    assert [tag["id"] for tag in owner_list.json()] == [work["id"]]
    assert other_list.json() == []

    for method in ("get", "patch", "delete"):
        response = await client.request(
            method,
            f"/api/v1/tags/{work['id']}",
            json={"name": "Other user edit"} if method == "patch" else None,
            headers=other_headers,
        )
        assert response.status_code == 404

    updated = await client.patch(
        f"/api/v1/tags/{work['id']}",
        json={"name": "Updated Work", "color": None},
        headers=owner_headers,
    )
    deleted = await client.delete(f"/api/v1/tags/{work['id']}", headers=owner_headers)

    assert updated.status_code == 200
    assert updated.json()["name"] == "Updated Work"
    assert updated.json()["color"] is None
    assert deleted.status_code == 204
    # Creating the Todo starts at version 1; only successful Tag mutations
    # advance the owner's list cache after that. Rejected cross-user/duplicate
    # requests must not make a cache version appear to have changed.
    assert await shared_redis.get(todo_cache_version_key(work["user_id"])) == "4"
    assert shared_redis.incr.await_count == 4


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_tag_mapping_is_owner_scoped_and_invalidates_cached_lists(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """A caller cannot attach another user's Tag or mutate another user's mapping."""
    owner_token = await get_auth_token(client, "mapping-api-owner@example.com")
    other_token = await get_auth_token(client, "mapping-api-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    owner_todo = await create_todo(client, owner_headers, "Owner Todo")
    other_todo = await create_todo(client, other_headers, "Other Todo")
    owner_tag = await create_tag(client, owner_headers, "Owner Tag")
    other_tag = await create_tag(client, other_headers, "Other Tag")
    await client.get("/api/v1/todos", headers=owner_headers)

    foreign_attach = await client.post(
        f"/api/v1/todos/{owner_todo['id']}/tags",
        json={"tag_id": other_tag["id"]},
        headers=owner_headers,
    )
    attached = await client.post(
        f"/api/v1/todos/{owner_todo['id']}/tags",
        json={"tag_id": owner_tag["id"]},
        headers=owner_headers,
    )
    duplicate = await client.post(
        f"/api/v1/todos/{owner_todo['id']}/tags",
        json={"tag_id": owner_tag["id"]},
        headers=owner_headers,
    )
    foreign_todo_attach = await client.post(
        f"/api/v1/todos/{other_todo['id']}/tags",
        json={"tag_id": owner_tag["id"]},
        headers=other_headers,
    )
    todo_with_tag = await client.get(
        f"/api/v1/todos/{owner_todo['id']}",
        headers=owner_headers,
    )
    foreign_detach = await client.delete(
        f"/api/v1/todos/{owner_todo['id']}/tags/{owner_tag['id']}",
        headers=other_headers,
    )
    detached = await client.delete(
        f"/api/v1/todos/{owner_todo['id']}/tags/{owner_tag['id']}",
        headers=owner_headers,
    )

    assert foreign_attach.status_code == 404
    assert attached.status_code == 204
    assert duplicate.status_code == 409
    assert foreign_todo_attach.status_code == 404
    assert [tag["id"] for tag in todo_with_tag.json()["tags"]] == [owner_tag["id"]]
    assert foreign_detach.status_code == 404
    assert detached.status_code == 204
    # Todo create + Tag create + successful attach + successful detach. Failed
    # owner-boundary checks and duplicate mapping must leave the version intact.
    assert await shared_redis.get(todo_cache_version_key(owner_todo["user_id"])) == "4"
    assert shared_redis.incr.await_count == 6


@pytest.mark.asyncio(loop_scope="session")
async def test_todo_filters_use_all_inputs_and_require_an_owned_tag(
    client: AsyncClient,
):
    """Status, tag, keyword, date, and pagination inputs produce isolated results."""
    token = await get_auth_token(client, "todo-filter-owner@example.com")
    other_token = await get_auth_token(client, "todo-filter-other@example.com")
    headers = {"Authorization": f"Bearer {token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    work = await create_tag(client, headers, "Work")
    home = await create_tag(client, headers, "Home")
    foreign_tag = await create_tag(client, other_headers, "Foreign")
    completed = await create_todo(
        client,
        headers,
        "Completed work item",
        description="match keyword",
    )
    active = await create_todo(
        client,
        headers,
        "Active home item",
        description="match keyword",
    )
    await create_todo(client, headers, "Unrelated item")
    for todo, tag in ((completed, work), (active, home)):
        response = await client.post(
            f"/api/v1/todos/{todo['id']}/tags",
            json={"tag_id": tag["id"]},
            headers=headers,
        )
        assert response.status_code == 204
    completed_response = await client.put(
        f"/api/v1/todos/{completed['id']}",
        json={"completed": True},
        headers=headers,
    )

    today = datetime.now(timezone.utc).date().isoformat()
    status_true = await client.get(
        "/api/v1/todos", params={"status": True}, headers=headers
    )
    status_false = await client.get(
        "/api/v1/todos", params={"status": False}, headers=headers
    )
    by_tag = await client.get(
        "/api/v1/todos", params={"tag_id": work["id"]}, headers=headers
    )
    by_keyword = await client.get(
        "/api/v1/todos", params={"keyword": "match"}, headers=headers
    )
    by_date = await client.get(
        "/api/v1/todos",
        params={"date_from": today, "date_to": today},
        headers=headers,
    )
    page_size_result = await client.get(
        "/api/v1/todos",
        params={"page": 1, "page_size": 1},
        headers=headers,
    )
    conflicting_page_sizes = await client.get(
        "/api/v1/todos",
        params={"size": 1, "page_size": 2},
        headers=headers,
    )
    future = (datetime.now(timezone.utc).date() + timedelta(days=1)).isoformat()
    future_date = await client.get(
        "/api/v1/todos",
        params={"date_from": future, "date_to": future},
        headers=headers,
    )
    foreign_filter = await client.get(
        "/api/v1/todos",
        params={"tag_id": foreign_tag["id"]},
        headers=headers,
    )
    invalid_range = await client.get(
        "/api/v1/todos",
        params={"date_from": future, "date_to": today},
        headers=headers,
    )

    assert completed_response.status_code == 200
    assert {item["id"] for item in status_true.json()["items"]} == {completed["id"]}
    assert {item["id"] for item in status_false.json()["items"]} == {
        active["id"],
        next(
            item["id"]
            for item in by_date.json()["items"]
            if item["title"] == "Unrelated item"
        ),
    }
    assert [item["id"] for item in by_tag.json()["items"]] == [completed["id"]]
    assert {item["id"] for item in by_keyword.json()["items"]} == {
        completed["id"],
        active["id"],
    }
    assert by_date.json()["total"] == 3
    assert page_size_result.json()["size"] == 1
    assert len(page_size_result.json()["items"]) == 1
    assert conflicting_page_sizes.status_code == 422
    assert future_date.json()["items"] == []
    assert foreign_filter.status_code == 404
    assert invalid_range.status_code == 422


@pytest.mark.asyncio(loop_scope="session")
async def test_bulk_status_update_is_atomic_owner_scoped_and_invalidates_cache(
    client: AsyncClient,
    shared_redis: MagicMock,
):
    """Bulk updates reject mixed ownership without changing any Todo."""
    owner_token = await get_auth_token(client, "bulk-owner@example.com")
    other_token = await get_auth_token(client, "bulk-other@example.com")
    owner_headers = {"Authorization": f"Bearer {owner_token}"}
    other_headers = {"Authorization": f"Bearer {other_token}"}
    first = await create_todo(client, owner_headers, "First bulk Todo")
    second = await create_todo(client, owner_headers, "Second bulk Todo")
    foreign = await create_todo(client, other_headers, "Foreign bulk Todo")
    await client.get("/api/v1/todos", headers=owner_headers)

    mixed_ownership = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], foreign["id"]], "completed": True},
        headers=owner_headers,
    )
    unchanged = await client.get(f"/api/v1/todos/{first['id']}", headers=owner_headers)
    updated = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [first["id"], second["id"]], "completed": True},
        headers=owner_headers,
    )
    refreshed = await client.get(
        "/api/v1/todos",
        params={"status": True},
        headers=owner_headers,
    )

    assert mixed_ownership.status_code == 404
    assert unchanged.json()["completed"] is False
    assert updated.status_code == 200
    assert updated.json() == {"updated_count": 2, "completed": True}
    assert {item["id"] for item in refreshed.json()["items"]} == {
        first["id"],
        second["id"],
    }
    # Only the owner's successful creates and bulk transaction invalidate their
    # cache; the rejected mixed-owner request cannot expose a partial update.
    assert await shared_redis.get(todo_cache_version_key(first["user_id"])) == "3"
    assert shared_redis.incr.await_count == 4
