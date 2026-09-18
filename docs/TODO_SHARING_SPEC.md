# Todo Sharing Technical Specification

## 1. Overview

Users can grant another registered user access to their todo list as a viewer or editor. The owner retains full control and can revoke access immediately.

Roles:

- Owner: reads and mutates todos, manages collaborators.
- Viewer: reads shared todos only.
- Editor: reads and updates shared todos, but cannot delete todos or manage access.

## 2. User Stories and Acceptance Criteria

### Share a todo list

As an owner, I want to share my list by email with viewer or editor permission.

- The recipient must be an existing user.
- Self-sharing is rejected.
- Repeating the same grant is idempotent; changing permission updates the existing grant.
- The recipient can access the list immediately after a successful response.

### Use a shared list

As a collaborator, I want to see lists shared with me.

- Viewers can list and read todos but receive 403 for mutations.
- Editors can create and update todos but cannot delete them or manage collaborators.
- All responses identify the list owner and the collaborator's effective permission.

### Revoke access

As an owner, I want to revoke a collaborator at any time.

- Revocation is owner-only and idempotent.
- Subsequent collaborator requests fail immediately.
- Owner and collaborator caches are invalidated before the response completes.

## 3. Scope

In scope: sharing an owner's complete todo list, viewer/editor roles, permission changes, revocation, collaborator listing, authorization and cache invalidation.

Out of scope: per-todo sharing, invitations for unregistered emails, public links, ownership transfer, nested groups, comments, notifications and offline conflict resolution.

## 4. Data Model

New table: `todo_list_shares`

| Column | Type | Rules |
|---|---|---|
| id | UUID | Primary key |
| owner_id | UUID | FK `users.id`, not null, cascade delete |
| collaborator_id | UUID | FK `users.id`, not null, cascade delete |
| permission | VARCHAR(10) | Check in (`viewer`, `editor`) |
| created_at | TIMESTAMPTZ | Not null, server default now |
| updated_at | TIMESTAMPTZ | Not null, updated on permission change |

Constraints:

- Unique `(owner_id, collaborator_id)`.
- Check `owner_id <> collaborator_id`.
- Index `(collaborator_id, updated_at DESC)` for shared-with-me queries.
- Index `(owner_id, updated_at DESC)` for collaborator management.

Existing todos remain keyed by `user_id`, which represents list ownership. This avoids rewriting rows when access changes.

## 5. API Contracts

| Method | Endpoint | Purpose | Allowed role |
|---|---|---|---|
| GET | `/api/v1/shares` | Lists collaborators | Owner |
| POST | `/api/v1/shares` | Creates or updates a grant | Owner |
| DELETE | `/api/v1/shares/{collaborator_id}` | Revokes a grant | Owner |
| GET | `/api/v1/shared-with-me` | Lists accessible owners | Collaborator |
| GET | `/api/v1/users/{owner_id}/todos` | Reads a shared list | Viewer, Editor |
| POST | `/api/v1/users/{owner_id}/todos` | Creates a shared todo | Editor |
| PUT | `/api/v1/users/{owner_id}/todos/{todo_id}` | Updates a shared todo | Editor |

Create/update grant request:

```json
{
  "collaborator_email": "collaborator@example.com",
  "permission": "viewer"
}
```

Success returns 201 for a new grant and 200 for a permission update. Errors use a consistent body: `{"detail": "message"}`.

- 400: self-share or invalid transition.
- 401: missing or invalid token.
- 403: authenticated but insufficient permission.
- 404: recipient, owner, todo or share not found. Cross-owner todo lookups also return 404.
- 409: conflicting concurrent grant update.
- 422: schema validation failure.

## 6. Authorization and Concurrency

Every shared todo query includes both `todos.user_id = owner_id` and a current share lookup. Permission is evaluated inside the request transaction; client-provided role data is never trusted.

Grant writes use the unique constraint as the final race-condition guard. Permission updates use `updated_at` as an optimistic concurrency token or lock the grant row with `SELECT FOR UPDATE`. Revocation and todo mutation serialize on the grant row so a mutation cannot commit after a completed revoke.

Editors cannot share onward, revoke access, delete todos, or modify ownership. Revoked collaborators receive 403 for the list endpoint and 404 for individual todo IDs.

## 7. Caching and Invalidation

Keys include owner, requester, permission version and query parameters:

`todos:shared:{owner_id}:{requester_id}:{share_updated_at}:{query_hash}`

Creating/updating/deleting a todo invalidates the owner's list keys and keys for all active collaborators. Creating, changing or revoking a grant invalidates both collaborator discovery and shared todo keys. Invalidation completes before the API reports success; short TTL remains a fallback, not the correctness mechanism.

## 8. Rollout and Observability

Deploy the additive migration first, then API and UI. Record grant changes in structured audit logs with actor, owner, collaborator, old/new role and request ID. Monitor 403/404 rates, invalidation failures and grant-write conflicts. No existing todo data migration is required.
