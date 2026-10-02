# Technical Specification: Todo Sharing

## 1. Overview

Owners can share an individual todo with an existing user as a `viewer` or `editor`, and revoke access at any time. The current API has todos, not list containers; sharing therefore applies per todo. Existing `GET /api/v1/todos` remains owner-only.

**Roles:** Owner controls and deletes the todo; editor reads and updates it; viewer reads it.

## 2. User Stories & Acceptance Criteria

### Share a todo

As an owner, I want to grant a registered user viewer or editor access so they can see or contribute to one todo.

- Owner can create a grant using the recipient's email and role.
- Email is trimmed and matched case-insensitively; unknown account returns `404`.
- Owner cannot share with themself (`422`). A duplicate grant returns `409`.
- Owner can change a grant's role or revoke it.

### Access a shared todo

As a collaborator, I want to find and read todos shared with me without seeing the owner's other todos.

- Shared list contains only active grants for the authenticated user and sorts by `created_at DESC, id DESC`.
- A collaborator can read a shared todo; a viewer cannot update it.
- An editor can update title, description, and completion status, but cannot delete or reshare it.
- A caller without a grant receives `404`, the same as for a nonexistent todo.

### Revoke access

As an owner, I want to revoke a grant so the collaborator loses access.

- Only the owner can manage grants or delete the todo.
- After revoke commits, subsequent collaborator requests are denied.
- Deleting a todo also deletes its grants.

## 3. Scope

**In scope:** Direct grants to existing users, viewer/editor roles, grant listing/creation/role change/revoke, shared todo list/detail, editor updates, owner-only deletion.

**Out of scope:** Pending invitations, email notifications, sharing whole lists, groups, public links, expiry, additional roles, ownership transfer, comments, and real-time collaboration.

## 4. Data Model

Add `todo_shares` (PostgreSQL):

| Field | Type | Constraints |
|---|---|---|
| `id` | UUID | Primary key |
| `todo_id` | UUID | Not null; FK to `todos.id`, `ON DELETE CASCADE` |
| `shared_with_user_id` | UUID | Not null; FK to `users.id`, `ON DELETE CASCADE` |
| `role` | VARCHAR(16) | Not null; check: `viewer` or `editor` |
| `created_at` | TIMESTAMPTZ | Not null, UTC |
| `updated_at` | TIMESTAMPTZ | Not null, UTC; update on role change |

- Unique constraint: (`todo_id`, `shared_with_user_id`) — at most one grant per recipient per todo.
- Index: (`shared_with_user_id`, `created_at`, `todo_id`) for shared-todo listing. The unique constraint also indexes (`todo_id`, `shared_with_user_id`); do not add a duplicate index.
- No owner column is stored; resolve ownership from `todos.user_id`.
- Deleting a todo or recipient account cascades to their grants. Owner-account deletion must follow the existing todo FK policy and remove owned todos and grants consistently.

## 5. API Design

All routes require a bearer access token. Prefix: `/api/v1`. IDs are UUIDs. Pagination uses `page` (default `1`) and `size` (default `20`, range `1–100`). Errors use `{"detail":"message"}`; schema validation uses the standard FastAPI `422` response.

| Method & endpoint | Purpose | Success |
|---|---|---|
| `POST /todos/{todo_id}/shares` | Grant access; owner only | `201` grant |
| `GET /todos/{todo_id}/shares` | List grants; owner only | `200` paginated grants |
| `PATCH /todos/{todo_id}/shares/{share_id}` | Change role; owner only | `200` grant |
| `DELETE /todos/{todo_id}/shares/{share_id}` | Revoke; owner only | `204` |
| `GET /shared-todos?page=&size=` | List todos shared with caller | `200` paginated todos |
| `GET /shared-todos/{todo_id}` | Read shared todo | `200` todo |
| `PUT /todos/{todo_id}` | Existing update; owner or editor | `200` todo |
| `DELETE /todos/{todo_id}` | Existing delete; owner only | `204` |

**Create request** `POST /todos/{todo_id}/shares`:

```json
{ "email": "user@example.com", "role": "viewer" }
```

`email` is required, valid, trimmed, and at most 255 characters. `role` is required and must be `viewer` or `editor`.

**Role update** `PATCH /todos/{todo_id}/shares/{share_id}`:

```json
{ "role": "editor" }
```

Shared todo response contains the normal todo fields plus `role` and `owner: { "id": "<uuid>", "email": "<email>" }`. List response: `{ "items": [], "total": 0, "page": 1, "size": 20 }`. Grant response contains `id`, `todo_id`, `shared_with_user_id`, `role`, `created_at`, and `updated_at`.

**Errors:** `401` invalid/missing token; `403` viewer write or non-owner management/delete; `404` missing todo/account/grant or no access (share-management requests for another user's todo also return `404`); `409` duplicate grant; `422` invalid input or self-sharing. Unexpected errors return `500` without internal details.

## 6. Authorization & Edge Cases

- Determine caller from the verified token. Check ownership or an active grant on every request; never rely on client-supplied user IDs or cached access as authorization.
- Permission matrix: owner reads/updates/deletes/manages grants; editor reads/updates; viewer reads; no grant has no access.
- Resolve recipient email at grant creation and store the user's UUID. Email changes do not change the grant. Collaborators cannot reshare.
- Self-sharing returns `422`. Duplicate grants return `409`; the database unique constraint handles concurrent duplicate requests.
- A collaborator update and revoke must lock/check the grant in the same transaction as the update. Whichever transaction obtains authorization first completes first; after revoke commits, later requests are denied. A request already committed before revoke cannot be undone.
- Use a consistent lock order (todo, then grant) for update, revoke, and delete operations to reduce deadlocks.
- Todo deletion cascades grants; requests after commit return `404`.

## 7. Caching & Revocation

- Keep the existing owner list cache scoped by owner ID. When an editor updates a todo, invalidate the **owner's** list cache.
- Do not cache shared list or detail responses in this release. Shared access is checked against the database on each request, so revoked users cannot receive stale cached todo content.
- After grant changes or todo deletion, invalidate any owner-side cached representation containing affected todo/share data before reporting success. Revocation takes effect in the database before success is returned; Redis is never proof of authorization.
- If shared-response caching is added later, keys must include collaborator and grant/version scope, and revocation must invalidate them before returning success.
