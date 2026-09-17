# Technical Specification: Todo List Sharing

## 1. Overview & Objective

- **Feature Summary**:
  Allow a user to share their todo list with another registered user with either `viewer` or `editor` permission. The owner can revoke access at any time.

- **Problem Statement**:
  The current Todo application only allows users to access and manage their own todos. Users cannot collaborate on a todo list or give another user controlled access.

- **Target Audience / Roles**:
  - **Owner**: Owns the todo list and manages sharing permissions.
  - **Viewer**: Can view the owner's todo list but cannot modify it.
  - **Editor**: Can view, create, update, toggle, and delete todos in the shared list.
  - **Admin**: Not included in this feature. Existing system administration remains unchanged.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Share Todo List

- **As a** Owner
- **I want to** share my todo list with another registered user
- **So that** they can access my todos with controlled permissions

- **Acceptance Criteria**:
  - [ ] Owner can share their todo list with another existing user.
  - [ ] Owner must specify either `viewer` or `editor` permission.
  - [ ] The target user must exist in the system.
  - [ ] Owner cannot share the list with themselves.
  - [ ] A user cannot have multiple active shares for the same owner.
  - [ ] A successful share returns `201 Created`.

### User Story 2: View Shared Todo List

- **As a** Viewer or Editor
- **I want to** view the owner's todo list
- **So that** I can see todos that have been shared with me

- **Acceptance Criteria**:
  - [ ] Viewer can list todos belonging to the owner.
  - [ ] Editor can list todos belonging to the owner.
  - [ ] Users without an active share cannot access the owner's todos.
  - [ ] Revoked users immediately lose access.
  - [ ] Access to one owner's list must not expose another owner's todos.

### User Story 3: Edit Shared Todo List

- **As a** Editor
- **I want to** create and modify todos in the shared list
- **So that** I can collaborate with the owner

- **Acceptance Criteria**:
  - [ ] Editor can create a todo under the owner's list.
  - [ ] Editor can update an existing todo belonging to the owner.
  - [ ] Editor can toggle the completed status.
  - [ ] Editor can delete a todo belonging to the owner.
  - [ ] Viewer cannot perform any write operation.
  - [ ] Users without an active share cannot perform any operation on the list.

### User Story 4: Manage Shared Access

- **As a** Owner
- **I want to** revoke or change another user's permission
- **So that** I can control who can access my todo list

- **Acceptance Criteria**:
  - [ ] Owner can revoke an active share.
  - [ ] Revocation immediately prevents further access.
  - [ ] Owner can change an existing user's permission from `viewer` to `editor` or vice versa.
  - [ ] Only the owner can manage shares for their list.
  - [ ] Revoked users must not continue receiving cached todo data.

---

## 3. Scope

### In-Scope

- Share one user's todo list with another registered user.
- `viewer` and `editor` permissions.
- Create, read, update and delete share records.
- Permission checks for shared todo access.
- Owner-only share management.
- Duplicate share prevention.
- Self-sharing prevention.
- Immediate permission enforcement after revocation.
- Cache invalidation when sharing permissions change.
- Timestamps on share records.

### Out-of-Scope

- Sharing individual todos.
- Sharing with users who do not have an account.
- Public todo lists or public share links.
- Email invitations or email notifications.
- Expiring shares.
- Group/team-based sharing.
- Nested sharing or permission delegation.
- Admin override functionality.
- Detailed activity/audit history.
- Real-time collaboration or WebSocket synchronization.
- Multiple permission levels beyond `viewer` and `editor`.

---

## 4. Database Design

### New Tables / Altered Tables

Add a new `todo_shares` table.

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | PK, NOT NULL | Unique share record ID |
| `owner_id` | UUID | FK → `users.id`, NOT NULL | User who owns the todo list |
| `shared_with_id` | UUID | FK → `users.id`, NOT NULL | User receiving access |
| `permission` | VARCHAR / ENUM | NOT NULL | `viewer` or `editor` |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Share creation time |
| `updated_at` | TIMESTAMP WITH TIME ZONE | NOT NULL | Last permission update time |

The existing `todos` table does not need to change.

Todos continue to belong to their original owner through the existing `user_id` relationship.

### Constraints & Indexes

#### Primary Key

`todo_shares.id`

#### Foreign Keys

- `todo_shares.owner_id` → `users.id` with `ON DELETE CASCADE`
- `todo_shares.shared_with_id` → `users.id` with `ON DELETE CASCADE`

If a user account is deleted, all share records where that user is either the owner or recipient are automatically removed.

#### Unique Constraint

`UNIQUE(owner_id, shared_with_id)`

This prevents multiple share records between the same owner and recipient.

#### Check Constraint

`permission IN ('viewer', 'editor')`

This prevents invalid permission values at database level.

#### Indexes

- `idx_todo_shares_owner_id` on `owner_id`
- `idx_todo_shares_shared_with_id` on `shared_with_id`

The unique constraint on `(owner_id, shared_with_id)` also provides an index useful for checking a specific sharing relationship.

The `shared_with_id` index supports queries for todo lists shared with the current user.

---

## 5. API Contracts & Endpoints

### Share Management

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todo-shares` | Share owner's todo list with another user | Yes |
| GET | `/api/v1/todo-shares` | List shares owned by current user | Yes |
| GET | `/api/v1/todo-shares/received` | List todo lists shared with current user | Yes |
| PATCH | `/api/v1/todo-shares/{share_id}` | Change viewer/editor permission | Yes |
| DELETE | `/api/v1/todo-shares/{share_id}` | Revoke access | Yes |

### Shared Todo Access

Existing Todo endpoints continue to be used, but authorization logic must be extended.

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| GET | `/api/v1/todos?owner_id={owner_id}` | List owner's todos when access is granted | Yes |
| POST | `/api/v1/todos?owner_id={owner_id}` | Create todo in owner's list | Yes |
| GET | `/api/v1/todos/{todo_id}` | Read a todo when access is granted | Yes |
| PUT | `/api/v1/todos/{todo_id}` | Update a todo when editor access is granted | Yes |
| DELETE | `/api/v1/todos/{todo_id}` | Delete a todo when editor access is granted | Yes |

The API must always derive the authenticated user from the JWT and must not trust a client-supplied user ID for authorization.

### Create Share Request

Example request:

`{ "shared_with_id": "uuid", "permission": "viewer" }`

Validation:

- `shared_with_id` must be a valid UUID.
- Target user must exist.
- `shared_with_id` must not equal the authenticated user's ID.
- `permission` must be either `viewer` or `editor`.

### Update Share Request

Example request:

`{ "permission": "editor" }`

### Share Response

Example response:

`{ "id": "uuid", "owner_id": "uuid", "shared_with_id": "uuid", "permission": "viewer", "created_at": "2026-09-17T10:00:00Z", "updated_at": "2026-09-17T10:00:00Z" }`

### Responses & Error Codes

#### 201 Created

Share created successfully.

#### 200 OK

Share retrieved or permission updated successfully.

#### 204 No Content

Share revoked successfully.

#### 400 Bad Request

Business validation failure.

Example:

`{ "detail": "Cannot share todo list with yourself" }`

#### 401 Unauthorized

Missing, invalid, or expired JWT.

Example:

`{ "detail": "Not authenticated" }`

#### 403 Forbidden

Authenticated user does not have sufficient permission.

Example:

`{ "detail": "Editor permission required" }`

#### 404 Not Found

Target user, share record, or todo does not exist or is not accessible.

Example:

`{ "detail": "Share not found" }`

For authorization-sensitive resources, returning `404` for an inaccessible todo is preferred to avoid revealing whether another user's todo exists.

#### 409 Conflict

Duplicate share.

Example:

`{ "detail": "Todo list is already shared with this user" }`

#### 422 Unprocessable Entity

Invalid request schema or field format.

---

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Action | Owner | Editor | Viewer | No Access |
|---|---:|---:|---:|---:|
| View shared todos | Yes | Yes | Yes | No |
| Create todo | Yes | Yes | No | No |
| Read todo | Yes | Yes | Yes | No |
| Update todo | Yes | Yes | No | No |
| Toggle completed | Yes | Yes | No | No |
| Delete todo | Yes | Yes | No | No |
| Create share | Yes | No | No | No |
| Change share permission | Yes | No | No | No |
| Revoke share | Yes | No | No | No |

The owner retains full access regardless of share records.

### Self-Sharing

A user must not be allowed to create a share where:

`owner_id == shared_with_id`

The API should reject this request with `400 Bad Request`.

This rule should be checked in application logic and enforced by a database constraint where practical.

### Duplicate Shares

When creating a share:

1. Check whether an active relationship already exists.
2. The database unique constraint on `(owner_id, shared_with_id)` is the final protection against concurrent duplicate inserts.
3. If a duplicate insert occurs, return `409 Conflict`.

### Permission Delegation

A shared user cannot share the owner's todo list with another user.

Only the actual owner can create, update, or revoke share records.

This prevents permission escalation through nested sharing.

### Concurrent Updates

Permission changes and todo mutations may happen concurrently.

Example:

1. User B has `editor` permission.
2. Owner revokes User B's access.
3. User B sends an update request at approximately the same time.

Every write request must check the current permission from the database within the request transaction.

The system must not rely only on a previously cached permission value.

If the permission check happens before revocation commits, the operation may complete. After revocation commits, subsequent requests must be rejected.

For stronger consistency requirements, the permission record and mutation can be protected using the same database transaction and appropriate row-level locking.

### Revoked Access

After revocation:

- New API requests from the revoked user must fail.
- Existing cached todo-list responses must be invalidated.
- The revoked user must not be able to access todos through direct todo IDs.
- The revoked user must not be able to modify or delete the owner's todos.

### Object-Level Authorization

Every Todo operation must verify one of:

- `authenticated_user.id == todo.user_id`
- `authenticated_user` has an active share for `todo.user_id`

For write operations, the share permission must be `editor`.

Authorization must be performed server-side for every request.

---

## 7. Caching & Invalidation Strategy

Todo list caching must include the requesting user's identity because two users may have different permissions for the same owner's list.

### Cache Key

Recommended format:

`todos:list:{requesting_user_id}:{owner_id}:{filters_hash}`

Example:

`todos:list:user-b:user-a:all`

This prevents a response generated for one user from being returned to another user.

### Permission Cache

If permissions are cached, use:

`todo-share:{owner_id}:{shared_with_id}`

The cached permission must have a short TTL and must be invalidated whenever the share changes.

### Cache Invalidation

#### Owner Creates a Share

Invalidate cache entries related to the recipient's access.

Invalidate:

`todo-share:{owner_id}:{shared_with_id}`

and any affected todo-list cache entries.

#### Owner Changes Permission

Invalidate:

`todo-share:{owner_id}:{shared_with_id}`

and the recipient's todo-list cache.

#### Owner Revokes Permission

Invalidate immediately:

`todo-share:{owner_id}:{shared_with_id}`

and all todo-list cache entries for the affected recipient/owner relationship.

The authorization check must still use authoritative database state when required. Cache invalidation is an optimization and must not be treated as the security boundary.

#### Todo Mutation

When an owner or editor creates, updates, toggles, or deletes a todo, invalidate list caches for:

- The owner.
- Users who currently have access to the owner's list.

For large numbers of collaborators, this should be handled carefully to avoid excessive cache deletion. A versioned cache namespace can be considered in a future optimization.

### Cache Consistency Requirement

A revoked user must not receive stale todo data from Redis after the revoke operation succeeds.

Database authorization remains the source of truth.

---

## 8. Implementation Notes

- Add `todo_shares` as a new SQLAlchemy model.
- Add an Alembic migration for the table, constraints, and indexes.
- Add Pydantic request/response schemas.
- Extend Todo authorization checks without changing the existing ownership model.
- Keep existing owner-only behavior unchanged.
- Add automated tests for:
  - Viewer can read but cannot modify.
  - Editor can read and modify.
  - Owner can revoke access.
  - Revoked user loses access immediately.
  - Self-sharing is rejected.
  - Duplicate sharing is rejected.
  - User cannot share another user's list.
  - Cross-user cache isolation.
  - Cache invalidation after permission changes.

---

## 9. Non-Functional Requirements

- Authorization checks must be performed server-side.
- API responses must not expose users' private todo lists without authorization.
- Database constraints must protect against duplicate share records.
- Permission revocation must take effect immediately for subsequent requests.
- Share-related queries should use indexed columns.
- Existing Todo functionality must remain backward compatible for owners.