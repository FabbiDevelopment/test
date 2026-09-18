# Todo Sharing Technical Specification

## Overview

Users can share a Todo list with another registered user as a `viewer` or `editor`. The existing product has one implicit list per user, so this release introduces explicit lists without changing ownership of existing todos.

## User stories and acceptance criteria

### Share a list

As an owner, I want to grant another user access to a list so that we can collaborate.

- Owner selects a registered user and a role.
- Owner cannot share a list with themself.
- A duplicate invite updates the existing role instead of creating a second membership.
- Owner sees the current member list and can change a member from viewer to editor or back.

### Read and edit shared work

As a viewer, I can read the shared list and its todos but cannot create, update, or delete them. As an editor, I can read, create, update, and delete todos in the shared list. Only the owner can manage members, delete the list, or transfer ownership.

### Revoke access

As an owner, I can revoke a member at any time. Subsequent requests by that member return `404`, and their cached list data is invalidated immediately.

## Scope

In scope: list membership, direct sharing with existing users, viewer/editor roles, revocation, audit-safe authorization, and cache invalidation.

Out of scope: email invitations, public links, notifications, nested teams, ownership transfer, comments, activity feeds, and offline synchronization.

## Data model

### `todo_lists`

| Field | Type | Rules |
|---|---|---|
| `id` | UUID | Primary key |
| `owner_id` | UUID | FK `users.id`, not null, indexed |
| `name` | VARCHAR(100) | Not null |
| `created_at`, `updated_at` | TIMESTAMPTZ | Not null |

`todos.list_id` becomes a not-null FK to `todo_lists.id`. Deleting a list cascades to its todos and memberships. Deleting a user cascades lists they own and memberships they hold.

### `todo_list_members`

| Field | Type | Rules |
|---|---|---|
| `list_id` | UUID | FK `todo_lists.id`, cascade delete |
| `user_id` | UUID | FK `users.id`, cascade delete |
| `role` | ENUM | `viewer` or `editor`, not null |
| `created_at`, `updated_at` | TIMESTAMPTZ | Not null |

Primary key and unique constraint: `(list_id, user_id)`. Indexes: `(user_id, list_id)` and `(list_id, role)`.

## API

| Method | Endpoint | Access | Result |
|---|---|---|---|
| `GET` | `/api/v1/lists/{list_id}/members` | Owner | `200` members |
| `PUT` | `/api/v1/lists/{list_id}/members/{user_id}` | Owner | `{ "role": "viewer" \| "editor" }`, `200` |
| `DELETE` | `/api/v1/lists/{list_id}/members/{user_id}` | Owner | `204` |
| `GET` | `/api/v1/lists/{list_id}/todos` | Owner/viewer/editor | `200` paginated todos |
| `POST` | `/api/v1/lists/{list_id}/todos` | Owner/editor | `201` |
| `PUT`, `DELETE` | `/api/v1/lists/{list_id}/todos/{todo_id}` | Owner/editor | `200` / `204` |

Errors use `{ "detail": "..." }`: `401` missing/invalid token, `403` authenticated but forbidden administrative operation, `404` hidden list/todo/member, and `422` invalid payload.

## Authorization and consistency

Every Todo query joins or scopes through `list_id` and an ownership/membership predicate. A request re-checks membership inside its database transaction, so an editor whose access was revoked concurrently cannot commit a later change. The owner is not represented as a membership row; this prevents accidentally revoking their own access.

## Caching

Cache keys include list ID, requester user ID, role/version, pagination, and filters. On Todo changes, invalidate every cached representation of that list. On role change or revoke, invalidate the list caches for the owner and affected member before the response completes.
