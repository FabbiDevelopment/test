import pytest
from httpx import AsyncClient


async def get_auth_token(client: AsyncClient, email: str = "taguser@example.com") -> str:
    """Helper to register and get auth token."""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": "password123"},
    )
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_create_tag_success(client: AsyncClient):
    """Test successful tag creation."""
    token = await get_auth_token(client, "tag_create@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"name": "Urgent", "color": "#ef4444"}
    response = await client.post("/api/v1/tags", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Urgent"
    assert data["color"] == "#ef4444"
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_tag_casing_rejected(client: AsyncClient):
    """Test duplicate tag names are rejected case-insensitively (e.g. 'Work' vs 'work')."""
    token = await get_auth_token(client, "tag_dup@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/tags", json={"name": "Work", "color": "#3b82f6"}, headers=headers)

    # Try creating with lowercase
    response = await client.post(
        "/api/v1/tags", json={"name": "work", "color": "#10b981"}, headers=headers
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]

    # Try creating with UPPERCASE
    response2 = await client.post(
        "/api/v1/tags", json={"name": "WORK", "color": "#f59e0b"}, headers=headers
    )
    assert response2.status_code == 409


@pytest.mark.asyncio
async def test_tag_cross_user_isolation(client: AsyncClient):
    """Test User B cannot see, modify, or delete User A's tags."""
    token_a = await get_auth_token(client, "tag_usera@example.com")
    token_b = await get_auth_token(client, "tag_userb@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a tag
    res_a = await client.post(
        "/api/v1/tags", json={"name": "SecretA", "color": "#10b981"}, headers=headers_a
    )
    tag_a_id = res_a.json()["id"]

    # User B lists tags -> SecretA should NOT appear
    res_b_list = await client.get("/api/v1/tags", headers=headers_b)
    assert res_b_list.status_code == 200
    tag_names = [t["name"] for t in res_b_list.json()["items"]]
    assert "SecretA" not in tag_names

    # User B tries to update User A's tag -> 404
    res_b_update = await client.patch(
        f"/api/v1/tags/{tag_a_id}",
        json={"name": "HackedTag"},
        headers=headers_b,
    )
    assert res_b_update.status_code == 404

    # User B tries to delete User A's tag -> 404
    res_b_delete = await client.delete(
        f"/api/v1/tags/{tag_a_id}", headers=headers_b
    )
    assert res_b_delete.status_code == 404


@pytest.mark.asyncio
async def test_attach_and_detach_tag_to_todo(client: AsyncClient):
    """Test attaching a tag to a todo and detaching it."""
    token = await get_auth_token(client, "tag_attach@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create todo
    todo_res = await client.post(
        "/api/v1/todos",
        json={"title": "Tag test todo", "description": "Testing tags"},
        headers=headers,
    )
    todo_id = todo_res.json()["id"]

    # Create tag
    tag_res = await client.post(
        "/api/v1/tags",
        json={"name": "Feature", "color": "#8b5cf6"},
        headers=headers,
    )
    tag_id = tag_res.json()["id"]

    # Attach tag
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )
    assert attach_res.status_code == 200
    attached_data = attach_res.json()
    assert len(attached_data["tags"]) == 1
    assert attached_data["tags"][0]["name"] == "Feature"

    # Verify GET /todos/{id} reflects the attached tag
    get_res = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
    assert len(get_res.json()["tags"]) == 1

    # Detach tag
    detach_res = await client.delete(
        f"/api/v1/todos/{todo_id}/tags/{tag_id}",
        headers=headers,
    )
    assert detach_res.status_code == 204

    # Verify GET /todos/{id} no longer has the tag
    get_res_after = await client.get(f"/api/v1/todos/{todo_id}", headers=headers)
    assert len(get_res_after.json()["tags"]) == 0


@pytest.mark.asyncio
async def test_cannot_attach_other_user_tag(client: AsyncClient):
    """Test User A cannot attach User B's tag to their todo."""
    token_a = await get_auth_token(client, "tag_owner_a@example.com")
    token_b = await get_auth_token(client, "tag_owner_b@example.com")
    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A todo
    todo_res = await client.post(
        "/api/v1/todos", json={"title": "User A todo"}, headers=headers_a
    )
    todo_id = todo_res.json()["id"]

    # User B tag
    tag_res = await client.post(
        "/api/v1/tags", json={"name": "UserBTag"}, headers=headers_b
    )
    tag_id = tag_res.json()["id"]

    # User A attempts to attach User B's tag -> 404
    attach_res = await client.post(
        f"/api/v1/todos/{todo_id}/tags",
        json={"tag_id": tag_id},
        headers=headers_a,
    )
    assert attach_res.status_code == 404


@pytest.mark.asyncio
async def test_filter_todos_by_tag_and_keyword(client: AsyncClient):
    """Test filtering todos by tag and by keyword."""
    token = await get_auth_token(client, "tag_filter@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create tag
    tag_res = await client.post(
        "/api/v1/tags", json={"name": "BackendTask"}, headers=headers
    )
    tag_id = tag_res.json()["id"]

    # Create 2 todos
    t1_res = await client.post(
        "/api/v1/todos",
        json={"title": "Implement Redis Cache", "description": "Add caching layer"},
        headers=headers,
    )
    t1_id = t1_res.json()["id"]

    t2_res = await client.post(
        "/api/v1/todos",
        json={"title": "Design Figma Mockup", "description": "UI design"},
        headers=headers,
    )
    t2_id = t2_res.json()["id"]

    # Attach tag to t1
    await client.post(
        f"/api/v1/todos/{t1_id}/tags",
        json={"tag_id": tag_id},
        headers=headers,
    )

    # Filter by tag
    tag_filter_res = await client.get(
        f"/api/v1/todos?tag_id={tag_id}", headers=headers
    )
    assert tag_filter_res.status_code == 200
    tag_items = tag_filter_res.json()["items"]
    assert any(t["id"] == t1_id for t in tag_items)
    assert not any(t["id"] == t2_id for t in tag_items)

    # Filter by keyword
    kw_res = await client.get(
        "/api/v1/todos?keyword=Figma", headers=headers
    )
    assert kw_res.status_code == 200
    kw_items = kw_res.json()["items"]
    assert any(t["id"] == t2_id for t in kw_items)
    assert not any(t["id"] == t1_id for t in kw_items)


@pytest.mark.asyncio
async def test_bulk_update_status(client: AsyncClient):
    """Test bulk updating completed status for multiple todos."""
    token = await get_auth_token(client, "tag_bulk@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    t1 = (await client.post("/api/v1/todos", json={"title": "Bulk 1"}, headers=headers)).json()
    t2 = (await client.post("/api/v1/todos", json={"title": "Bulk 2"}, headers=headers)).json()
    t3 = (await client.post("/api/v1/todos", json={"title": "Bulk 3"}, headers=headers)).json()

    assert not t1["completed"]
    assert not t2["completed"]
    assert not t3["completed"]

    # Bulk update t1 and t2 to completed=True
    bulk_res = await client.patch(
        "/api/v1/todos/bulk-status",
        json={"todo_ids": [t1["id"], t2["id"]], "completed": True},
        headers=headers,
    )
    assert bulk_res.status_code == 200
    assert bulk_res.json()["updated_count"] == 2
    assert bulk_res.json()["completed"] is True

    # Verify t1 and t2 are completed, t3 is still incomplete
    t1_check = (await client.get(f"/api/v1/todos/{t1['id']}", headers=headers)).json()
    t2_check = (await client.get(f"/api/v1/todos/{t2['id']}", headers=headers)).json()
    t3_check = (await client.get(f"/api/v1/todos/{t3['id']}", headers=headers)).json()

    assert t1_check["completed"] is True
    assert t2_check["completed"] is True
    assert t3_check["completed"] is False


@pytest.mark.asyncio
async def test_tag_deletion_cascades_to_todo_tags_without_deleting_todo(client: AsyncClient):
    """Test deleting a tag removes the association but preserves the todo."""
    token = await get_auth_token(client, "tag_cascade@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # Create todo and tag
    todo = (await client.post("/api/v1/todos", json={"title": "Keep Me"}, headers=headers)).json()
    tag = (await client.post("/api/v1/tags", json={"name": "TemporaryTag"}, headers=headers)).json()

    # Attach tag
    await client.post(
        f"/api/v1/todos/{todo['id']}/tags",
        json={"tag_id": tag["id"]},
        headers=headers,
    )

    # Delete tag
    del_res = await client.delete(f"/api/v1/tags/{tag['id']}", headers=headers)
    assert del_res.status_code == 204

    # Verify todo still exists and has 0 tags
    todo_after = (await client.get(f"/api/v1/todos/{todo['id']}", headers=headers)).json()
    assert todo_after["id"] == todo["id"]
    assert len(todo_after["tags"]) == 0


@pytest.mark.asyncio
async def test_tag_caching_and_invalidation(client: AsyncClient):
    """Test tag list caching in Redis and invalidation on create/update/delete."""
    token = await get_auth_token(client, "tag_cache@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Initial empty list (populates cache)
    res1 = await client.get("/api/v1/tags", headers=headers)
    assert res1.status_code == 200
    assert len(res1.json()["items"]) == 0

    # 2. Create tag -> invalidates cache
    create_res = await client.post(
        "/api/v1/tags", json={"name": "CacheTag", "color": "#123456"}, headers=headers
    )
    assert create_res.status_code == 201
    tag_id = create_res.json()["id"]

    # 3. List tags -> should reflect newly created tag immediately (cache invalidated)
    res2 = await client.get("/api/v1/tags", headers=headers)
    assert len(res2.json()["items"]) == 1
    assert res2.json()["items"][0]["name"] == "CacheTag"

    # 4. Update tag -> invalidates cache
    update_res = await client.patch(
        f"/api/v1/tags/{tag_id}", json={"name": "UpdatedTag"}, headers=headers
    )
    assert update_res.status_code == 200

    # 5. List tags -> returns updated name immediately
    res3 = await client.get("/api/v1/tags", headers=headers)
    assert res3.json()["items"][0]["name"] == "UpdatedTag"

    # 6. Delete tag -> invalidates cache
    del_res = await client.delete(f"/api/v1/tags/{tag_id}", headers=headers)
    assert del_res.status_code == 204

    # 7. List tags -> empty list
    res4 = await client.get("/api/v1/tags", headers=headers)
    assert len(res4.json()["items"]) == 0

