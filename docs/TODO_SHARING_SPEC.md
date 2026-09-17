# Todo Sharing Technical Specification

## 1. Objective

Allow a todo owner to share the owner's todo list with another registered user as either `viewer` or `editor`, and revoke access immediately. The first release shares the complete list; it does not introduce per-item sharing.

## 2. Roles and User Stories

- As an owner, I can invite another user by email with viewer or editor permission.
- As an owner, I can list current shares and revoke one at any time.
- As a viewer, I can list shared todos but cannot create, update, or delete them.
- As an editor, I can create, update, and delete todos in a shared list, but cannot manage sharing.
- As a recipient, I can see who shared a list and my effective permission.

### Acceptance criteria

1. A valid invitation creates one pending/active share for the owner and recipient.
2. Self-sharing returns `409` and does not create a row.
3. A duplicate active share updates only through an explicit share update endpoint; a second create returns `409`.
4. Viewer GET list/detail succeeds; viewer mutations return `403`.
5. Editor todo mutations succeed while the share is active.
6. Revocation makes the next request fail immediately with `403` or `404`; all owner and recipient list/detail cache keys are invalidated in the same transaction boundary.
7. Deleted owners or recipients cascade/delete the share according to the data model.
8. The owner remains the only user allowed to grant, change, or revoke access.

## 3. Scope

In scope: direct user-to-user sharing, viewer/editor roles, list/detail and todo mutation authorization, share listing, permission update, revoke, audit timestamps, Redis invalidation.

Out of scope: public links, invitations to unregistered email addresses, nested sharing, teams/groups, notifications, expiration dates, per-todo permissions, comments, and UI role administration beyond the listed endpoints.

## 4. Data Model

### `todo_list_shares`

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key, generated server-side |
| `owner_id` | UUID | Not null, FK `users.id`, `ON DELETE CASCADE` |
| `recipient_id` | UUID | Not null, FK `users.id`, `ON DELETE CASCADE` |
| `role` | VARCHAR(16) | Not null, enum/check in `viewer`, `editor` |
| `created_at` | TIMESTAMPTZ | Not null |
| `updated_at` | TIMESTAMPTZ | Not null |
| `revoked_at` | TIMESTAMPTZ nullable | Null means active |

Constraints and indexes:

- Unique active share `(owner_id, recipient_id)` enforced with a PostgreSQL partial unique index where `revoked_at IS NULL`.
- Check `owner_id <> recipient_id`.
- Index `(recipient_id, revoked_at)` for shared-list discovery.
- Index `(owner_id, revoked_at)` for owner management.
- Foreign keys cascade on user deletion. Todo rows remain owned by the owner and are not reassigned.

## 5. API Contract

All endpoints use `/api/v1`, Bearer access tokens, and the existing JSON error shape `{ "detail": "..." }`.

| Method | Endpoint | Description | Success |
|---|---|---|---|
| `POST` | `/todo-shares` | Create a share by recipient email | `201` |
| `GET` | `/todo-shares/owned` | List shares created by current user | `200` |
| `GET` | `/todo-shares/shared-with-me` | List active lists shared with current user | `200` |
| `PATCH` | `/todo-shares/{share_id}` | Change `role` or revoke/restore according to policy | `200` |
| `DELETE` | `/todo-shares/{share_id}` | Revoke an active share | `204` |
| `GET` | `/shared-todos/{owner_id}` | List owner todos if recipient has active access | `200` |
| `GET` | `/shared-todos/{owner_id}/{todo_id}` | Read one shared todo | `200` |
| `POST` | `/shared-todos/{owner_id}` | Create todo, editor only | `201` |
| `PUT` | `/shared-todos/{owner_id}/{todo_id}` | Update todo, editor only | `200` |
| `DELETE` | `/shared-todos/{owner_id}/{todo_id}` | Delete todo, editor only | `204` |

Create request:

```json
{ "recipient_email": "person@example.com", "role": "viewer" }
```

Update request:

```json
{ "role": "editor" }
```

Response fields: `id`, `owner_id`, `recipient_id`, `recipient_email`, `role`, `created_at`, `updated_at`, `revoked_at`.

Errors: `401` missing/invalid/expired access token; `403` authenticated but not owner or insufficient role; `404` share/todo/recipient not found; `409` self-share or duplicate active share; `422` invalid UUID, email, or role.

## 6. Authorization and Edge Cases

- Resolve the recipient server-side by normalized email; never accept a recipient user ID without checking it belongs to the intended account.
- Owner can manage only shares where `owner_id = current_user.id`.
- A user cannot share with self. A recipient cannot re-share another user's list.
- Duplicate active create is rejected atomically by the partial unique index; the API maps the database conflict to `409`.
- Concurrent revoke/update is serialized by updating the share row and checking `revoked_at` in the same transaction. Authorization reads the current row, so a revoked share cannot authorize a later request.
- Todo mutation queries include owner ID and shared-list authorization in the same transaction. A missing row is returned as `404` to avoid revealing another user's data.
- Revoke invalidates `todos:list:{owner_id}:*`, `shared-todos:{owner_id}:{recipient_id}:*`, and relevant share-list keys after commit. A failed transaction must not publish invalidation for a change that did not persist.
- Role changes invalidate the same keys. Existing access tokens do not carry permissions; authorization is evaluated from the database on each request or from a short-lived cache with explicit invalidation.

## 7. Rollout and Observability

Create the table/indexes with an Alembic migration. For a large production table, create indexes concurrently in a separate migration step where supported and avoid long transactions. Log share create, role change, and revoke with actor, owner, recipient, share ID, result, and request ID; never log tokens.

## 8. Out of Scope

No email delivery, invitation acceptance workflow, public URL, group permissions, admin override, share expiration, per-item ACL, activity feed, or offline permission resolution in this release.
