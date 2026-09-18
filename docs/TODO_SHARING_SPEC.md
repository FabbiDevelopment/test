# Todo sharing specification

## Scope

This document defines a future sharing feature. No sharing tables or endpoints are implemented in this change.

## User stories and acceptance criteria

| User story | Acceptance criteria |
|---|---|
| As an owner, I can invite another registered user to a todo. | An owner can create one pending invite per todo and invitee; a non-owner receives 403. |
| As an invitee, I can accept or decline an invite. | Only the invitee can act on a pending invite; accepting grants the selected access level. |
| As a collaborator, I can view a shared todo. | A collaborator can read only the todos shared with them and only at the granted level. |
| As an owner, I can revoke access. | Revocation immediately prevents reads and writes and removes cached shared-list results. |

## Data model

| Table | Fields and constraints |
|---|---|
| `todo_shares` | `id UUID PK`; `todo_id UUID FK todos.id ON DELETE CASCADE`; `invitee_id UUID FK users.id ON DELETE CASCADE`; `role VARCHAR(10) NOT NULL` (`viewer` or `editor`); `status VARCHAR(10) NOT NULL` (`pending`, `accepted`, `declined`, `revoked`); `created_at TIMESTAMPTZ NOT NULL`; `updated_at TIMESTAMPTZ NOT NULL`; `UNIQUE(todo_id, invitee_id)`; index on `(invitee_id, status)`. |

## API

| Endpoint | Request | Success | Errors |
|---|---|---|---|
| `POST /api/v1/todos/{todo_id}/shares` | `{email, role}` | 201 pending share | 400 self-invite, 403 non-owner, 404 user/todo absent, 409 duplicate |
| `GET /api/v1/todos/shared-with-me` | pagination | 200 list | 401 unauthenticated |
| `PATCH /api/v1/shares/{share_id}` | `{status}` | 200 updated share | 403 not invitee/owner, 409 no longer pending |
| `DELETE /api/v1/shares/{share_id}` | none | 204 | 403 non-owner |

## Authorization and edge cases

- Every mutation validates the authenticated user and todo ownership or share role server-side.
- Reject self-invites and duplicate invites case-insensitively by the unique constraint.
- Use a transaction and row locking when accepting or revoking so concurrent actions cannot grant inconsistent access.
- Cache keys for owned and shared lists include user ID and filters. Invalidate both parties' affected keys after invite, acceptance, decline, or revocation.
- Out of scope: email delivery, groups, public links, audit exports, and notifications.
