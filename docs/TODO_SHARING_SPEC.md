# Technical Specification: Todo Sharing (Chia sẻ việc cần làm)

> Level 3A — Production-ready spec. Template: `templates/SPEC_TEMPLATE.md`

## 1. Overview

- **Feature**: Owner share todo(s) với user khác — quyền **viewer** (read-only) hoặc **editor** (read-write). Owner **revoke** bất cứ lúc nào.
- **Problem**: Hiện tại todo thuộc một owner — chưa collaboration.
- **Roles**: Owner, Viewer, Editor.

## 2. User Stories & Acceptance Criteria

### US-1: Share as viewer
- Owner invite user đã tồn tại → viewer thấy todo, **không** PUT/DELETE/re-share.

### US-2: Share as editor
- Editor PUT được (title, description, completed), **không** DELETE/revoke/share tiếp.

### US-3: Revoke access
- Revoke **immediate** → 403; invalidate Redis cache viewer/editor ngay.

### US-4: Shared list
- `GET /todos?scope=shared` + field `permission`, `owner_email`.

## 3. Scope

**In-scope v1**: share per-todo hoặc all todos; viewer/editor; revoke; cache invalidation; chặn self-share & duplicate invite.

**Out-of-scope v1**: public link; invite email chưa register; admin role; audit log; team groups; expiring shares.

## 4. Database — `todo_shares`

| Column | Type | Notes |
|--------|------|-------|
| id | UUID PK | |
| todo_id | UUID FK todos, nullable | NULL = share all todos |
| owner_id | UUID FK users | CASCADE |
| shared_with_id | UUID FK users | CASCADE |
| permission | VARCHAR CHECK viewer/editor | |
| created_at, updated_at | TIMESTAMPTZ | |

**Unique**: `(owner_id, shared_with_id, todo_id)`; partial unique khi `todo_id IS NULL`.

**Indexes**: `shared_with_id`, `todo_id`, `owner_id`.

## 5. API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/shares` | Create share |
| GET | `/api/v1/shares` | Owner's shares |
| GET | `/api/v1/shares/received` | Received shares |
| PATCH | `/api/v1/shares/{id}` | Change permission |
| DELETE | `/api/v1/shares/{id}` | Revoke |

**Errors**: 400 self-share; 404 user not found; 409 duplicate; 403 unauthorized.

## 6. Authorization Matrix

| Action | Owner | Viewer | Editor | Other |
|--------|-------|--------|--------|-------|
| GET | ✓ | ✓ | ✓ | ✗ |
| PUT | ✓ | ✗ | ✓ | ✗ |
| DELETE | ✓ | ✗ | ✗ | ✗ |

**Edge cases**: revoke during editor PUT → transaction + re-check permission; no re-share by collaborator.

## 7. Cache invalidation

Keys: `todos:list:{user_id}:{scope}:...`, `shares:received:{user_id}`.

Invalidate on: share create, revoke, shared todo update, permission change.

## 8. Out of scope (release boundaries)

Notifications, public URLs, nested sharing, share tags without todos.
