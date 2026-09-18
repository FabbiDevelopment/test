# Technical Specification: Todo List Sharing

## 1. Overview and objective

Allow a user to share their entire todo collection with another registered user as a viewer or editor and revoke that access at any time. A grant applies to the owner's current and future todos.

Today every query is scoped to `todos.user_id == current_user.id`. Collaboration requires copying data outside the product, which creates stale duplicates and no enforceable authorization boundary.

Roles:

- **Owner:** owns the list and every todo whose `user_id` is the owner's ID.
- **Viewer:** can list/read the owner's todos.
- **Editor:** has viewer rights and can create/update todos in the owner's list.
- **Unaffiliated user:** receives no evidence that the list or a todo exists.

Success means authorization comes from current database state, revocation applies on the next request, caches cannot leak across users/lists, duplicate/self shares are deterministic, and existing private-list behavior remains compatible.

## 2. User stories and acceptance criteria

### US-1: Share a list

As an owner, I want to share my todo list with a registered user as viewer or editor.

- A valid request creates exactly one active grant between owner and recipient.
- `role` accepts only `viewer` or `editor`; clients cannot grant owner rights.
- Sharing with oneself returns `422 SELF_SHARE_NOT_ALLOWED`.
- Unknown recipient returns `404 USER_NOT_FOUND` only after owner authentication.
- An existing grant returns `409 SHARE_ALREADY_EXISTS`; role changes use `PATCH`.
- The grant automatically covers existing and future todos owned by the owner.

### US-2: Discover and view shared lists

As a recipient, I want to see which users shared lists with me and open their todos.

- Active grants are paginated and identify owner, role, and grant timestamps.
- Viewer/editor can list and read the selected owner's todos.
- Responses expose `owner_id`, `owner_email`, and the caller's `access_role` so ownership is unambiguous.
- Revoked grants disappear on the next request.
- Todo pagination is deterministic: `created_at DESC, id DESC`.

### US-3: Edit a shared list

As an editor, I want to add and update todos in the owner's list.

- Owner/editor may create todos in that list and update title, description, or completion.
- Todos created by an editor retain `user_id = owner_id`; optionally record `created_by_user_id` in a later audit feature.
- Viewer receives `403 INSUFFICIENT_PERMISSION` for mutations.
- Editor cannot delete todos, manage grants, transfer ownership, or re-share.
- Partial updates preserve omitted fields and honor explicit `false`/`null`.

### US-4: Change or revoke access

As an owner, I want to change a recipient's role or revoke access immediately.

- Only the owner may list/update/delete outgoing grants.
- Repeating the current role is idempotent and returns `200`.
- Revocation deletes the grant and returns `204`.
- Authorization checks current database state inside mutation transactions.
- Owner and recipient list/detail/access caches are invalidated after commit; revocation invalidation completes before success is returned.

### US-5: Preserve owner control

As an owner, I retain destructive control over my list.

- Only owner may delete todos.
- Deleting one todo does not revoke the list grant.
- Deleting the owner account cascades its outgoing grants and todos.
- Deleting a recipient account cascades grants received by that user.

## 3. Scope

In scope:

- Share with an existing user by normalized email.
- Viewer/editor list-level roles.
- List outgoing grants and lists shared with the current user.
- Change role and revoke access.
- Shared todo list/read and editor create/update.
- Authorization, stable pagination, cache invalidation, concurrency, rollout, and observability.

Out of scope:

- Share-by-email invitations for unregistered users.
- Per-todo grants, multiple named lists, public links, teams/groups, nested sharing, ownership transfer, comments, notifications, real-time presence, and offline conflict resolution.
- Editor deletion and field-level permissions.
- Historical permission-audit UI (security logs still record events).

## 4. Data model

### Enum `todo_share_role`

`viewer | editor`.

### Table `todo_list_shares`

| Column | PostgreSQL type | Null | Description |
|---|---|---:|---|
| `id` | UUID | No | PK, application-generated UUID v4 |
| `owner_id` | UUID | No | FK `users.id ON DELETE CASCADE` |
| `recipient_id` | UUID | No | FK `users.id ON DELETE CASCADE` |
| `role` | `todo_share_role` | No | Viewer or editor |
| `created_at` | TIMESTAMPTZ | No | Grant creation, UTC |
| `updated_at` | TIMESTAMPTZ | No | Last role update, UTC |

Constraints and indexes:

- Primary key `(id)`.
- Unique `(owner_id, recipient_id)` closes duplicate-invite races and is the outgoing-grant lookup index.
- Check `owner_id <> recipient_id` enforces no self-share even if application validation is bypassed.
- Index `(recipient_id, created_at DESC, id DESC)` supports stable shared-with-me pagination.
- Optional index `(owner_id, created_at DESC, id DESC)` is added only if grant-management pagination needs ordering beyond the unique index.
- No standalone role index initially because cardinality is low.

This additive table needs no backfill. Migration order: create enum, table, constraints, then indexes. On large deployments, create non-constraint indexes concurrently. Downgrade drops the table before the enum.

## 5. API contracts

All routes use `/api/v1` and require a valid access token.

| Method | Endpoint | Permission | Success |
|---|---|---|---|
| POST | `/todo-shares` | Owner (current user) | `201` |
| GET | `/todo-shares?page=&page_size=` | Owner (current user) | `200` |
| PATCH | `/todo-shares/{share_id}` | Grant owner | `200` |
| DELETE | `/todo-shares/{share_id}` | Grant owner | `204` |
| GET | `/shared-todo-lists?page=&page_size=` | Recipient | `200` |
| GET | `/shared-todo-lists/{owner_id}/todos?page=&page_size=` | Viewer/editor | `200` |
| POST | `/shared-todo-lists/{owner_id}/todos` | Editor | `201` |
| GET | `/todos/{todo_id}` | Owner/viewer/editor | `200` |
| PUT | `/todos/{todo_id}` | Owner/editor | `200` |
| DELETE | `/todos/{todo_id}` | Owner only | `204` |

Static routes must be registered before `/todos/{todo_id}`-style dynamic routes.

### Create grant

```json
{
  "recipient_email": "collaborator@example.com",
  "role": "viewer"
}
```

Normalize email consistently with registration, validate role as an enum, and reject extra fields. Response:

```json
{
  "id": "uuid",
  "owner": {"id": "uuid", "email": "owner@example.com"},
  "recipient": {"id": "uuid", "email": "collaborator@example.com"},
  "role": "viewer",
  "created_at": "2026-09-19T00:00:00Z",
  "updated_at": "2026-09-19T00:00:00Z"
}
```

### Change role

```json
{"role": "editor"}
```

Only `role` is accepted. Repeating the current role returns the current resource.

### Shared lists response

```json
{
  "items": [
    {
      "owner": {"id": "uuid", "email": "owner@example.com"},
      "access_role": "viewer",
      "shared_at": "2026-09-19T00:00:00Z"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

For all pagination, `page >= 1` and `1 <= page_size <= 100`.

### Error envelope

```json
{
  "detail": {
    "code": "INSUFFICIENT_PERMISSION",
    "message": "Editor permission is required",
    "request_id": "uuid"
  }
}
```

| Status | Code | Condition |
|---:|---|---|
| 401 | `UNAUTHENTICATED` | Missing/invalid/expired access token |
| 403 | `INSUFFICIENT_PERMISSION` | Caller can see list but role cannot perform action |
| 404 | `LIST_NOT_FOUND` | Owner absent or caller has no relationship to list |
| 404 | `TODO_NOT_FOUND` | Todo absent or caller has no visibility |
| 404 | `USER_NOT_FOUND` | Owner supplied unknown recipient email |
| 404 | `SHARE_NOT_FOUND` | Owner supplied unknown grant ID |
| 409 | `SHARE_ALREADY_EXISTS` | Unique owner/recipient conflict |
| 409 | `SHARE_CHANGED` | Optional optimistic concurrency conflict |
| 422 | `SELF_SHARE_NOT_ALLOWED` | Owner equals recipient |
| 422 | `VALIDATION_ERROR` | Schema validation failure |

Use `404`, not `403`, for unaffiliated callers to prevent ID enumeration.

## 6. Authorization and concurrency

| Action | Owner | Editor | Viewer | Unaffiliated |
|---|:---:|:---:|:---:|:---:|
| List/read todos | Yes | Yes | Yes | No |
| Create/update todos | Yes | Yes | No | No |
| Delete todos | Yes | No | No | No |
| List/manage grants | Yes | No | No | No |
| Re-share/transfer | No | No | No | No |

- Never trust client-provided owner/role or cached permission alone.
- Shared todo queries require `todo.user_id = grant.owner_id`; knowing a todo ID is insufficient.
- Mutations include authorization in the SQL predicate within the same transaction as the write.
- Grant creation catches unique violations and returns `409`, closing check-then-insert races.
- Role update/revoke locks the grant row with `SELECT ... FOR UPDATE`.
- An editor update racing with revoke re-checks the grant in its write transaction. Lock acquisition order is owner/list grant then todo to avoid deadlocks.
- Rate-limit grant mutation and recipient email lookup to reduce enumeration/abuse.
- Bearer headers avoid cookie CSRF, but XSS remains important while tokens are stored in browser storage.

## 7. Cache and invalidation

Keys include both effective list owner and requesting user:

- `todos:owner:{owner_id}:viewer:{requester_id}:v{version}:{filters_hash}`
- `shared-lists:{recipient_id}:v{version}:{page}`
- `outgoing-shares:{owner_id}:v{version}:{page}`
- `todo:{todo_id}:viewer:{requester_id}:v{version}`
- `list-access:{owner_id}:{recipient_id}` with short TTL only as an optimization, never sole write authorization

After transaction commit:

- Create grant: invalidate recipient shared-list/access data and owner outgoing grants.
- Role change: invalidate recipient list/detail/access and owner outgoing grants.
- Revoke: synchronously invalidate recipient shared-list, all owner-list/detail variants, and access before returning success.
- Todo create/update/delete: invalidate owner's views and every active recipient's relevant list/detail versions.

Use an outbox consumer for reliable high-volume fan-out, but revocation also performs synchronous targeted invalidation. Cache failure must fail closed for access decisions and never restore revoked rights.

## 8. Observability, rollout, and rollback

- Structured events: grant created, role changed, revoked, denied mutation; include actor/owner/recipient/share IDs but no credentials.
- Metrics: endpoint latency/error, unique conflicts, denied access, invalidation failures, and cache hit rate.
- Deploy additive migration first, then read-compatible code behind feature flags.
- Enable viewer sharing, monitor, then enable editor writes separately.
- Rollback disables new grants/editor writes first. Existing rows can remain dormant; data removal is a later deliberate migration.

## 9. Test strategy

- Schema/unit: enum, self-share, email normalization, omitted versus explicit-null updates.
- API integration: grant CRUD, duplicate invites/casing, full role matrix, unaffiliated `404`, user deletion cascade.
- Collection behavior: existing and newly created todos appear under the same grant; editor-created todo belongs to owner.
- Concurrency: simultaneous duplicate invites, revoke racing editor update, downgrade racing update.
- Cache: immediate denial and all affected list/detail variants invalidated after revoke.
- E2E: owner grants viewer, upgrades to editor, recipient edits, owner revokes, recipient loses access without logout.

## 10. Open decisions

- Whether editor-created todos need `created_by_user_id` in v1 for audit attribution.
- Whether role updates require ETag/`If-Match` optimistic concurrency in v1.
- Security-event retention and whether recipient email may appear in owner audit exports.
