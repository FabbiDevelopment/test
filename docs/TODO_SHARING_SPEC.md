# Technical Specification: Todo Sharing

## 1. Overview & Objective
- **Feature Summary**: Allows users to share specific todo items with other users by email, granting them either read-only (`viewer`) or edit (`editor`) permissions. Owners can manage and revoke these permissions at any time.
- **Problem Statement**: Users currently have isolated todo lists. Collaboration requires a way to selectively share tasks without granting access to the entire account.
- **Target Audience / Roles**:
  - **Owner**: The creator of the todo item.
  - **Viewer**: A user granted read-only access to a shared todo.
  - **Editor**: A user granted read and update access to a shared todo.

## 2. User Stories & Acceptance Criteria

### User Story 1: Share a Todo
- **As an** Owner
- **I want to** share my todo item with another user via their email and assign a role (`viewer` or `editor`)
- **So that** they can view or collaborate on my task.
- **Acceptance Criteria**:
  - [ ] Owner can input a target email and role.
  - [ ] System verifies the target email exists.
  - [ ] System prevents the owner from sharing with themselves.
  - [ ] System prevents duplicate shares (upsert behavior if changing role).

### User Story 2: Revoke Access
- **As an** Owner
- **I want to** revoke access from a previously shared user
- **So that** they can no longer view or edit the task.
- **Acceptance Criteria**:
  - [ ] Owner can remove a user's access from a todo.
  - [ ] The revoked user immediately loses access (403 Forbidden).

### User Story 3: View & Edit Shared Todos
- **As a** Collaborator (Viewer/Editor)
- **I want to** view and/or edit the shared todo
- **So that** I can track or update the task's progress.
- **Acceptance Criteria**:
  - [ ] Both Viewers and Editors can read the todo.
  - [ ] Only Editors (and the Owner) can update the title, description, or completed status.
  - [ ] Neither Viewers nor Editors can delete the todo entirely or share it with others (only the Owner can).

## 3. Scope
- **In-Scope**: Sharing individual todos by email, role-based access control (`viewer`, `editor`), revoking access, listing todos shared with me.
- **Out-of-Scope**: Group/team sharing, sharing an entire list/folder of todos, public link sharing, email notifications upon sharing.

## 4. Database Design

### New Table: `todo_shares`
- **id**: UUID, Primary Key, default `uuid4()`
- **todo_id**: UUID, Foreign Key referencing `todos(id)` ON DELETE CASCADE
- **user_id**: UUID, Foreign Key referencing `users(id)` ON DELETE CASCADE
- **role**: VARCHAR(20) (enum: `'viewer'`, `'editor'`), NOT NULL
- **created_at**: TIMESTAMPTZ, NOT NULL, default `now()`
- **updated_at**: TIMESTAMPTZ, NOT NULL, default `now()`

### Constraints & Indexes
- **Unique Constraint**: `UNIQUE(todo_id, user_id)` — a user can only have one permission level per todo.
- **Indexes**:
  - `CREATE INDEX ix_todo_shares_todo_id ON todo_shares(todo_id);`
  - `CREATE INDEX ix_todo_shares_user_id ON todo_shares(user_id);`
  - `CREATE INDEX ix_todos_user_id_completed_created_at ON todos(user_id, completed, created_at);` (General performance).

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todos/{todo_id}/share` | Share a todo or update role | Yes (Owner only) |
| DELETE | `/api/v1/todos/{todo_id}/share/{user_id}` | Revoke access | Yes (Owner only) |
| GET | `/api/v1/todos/shared-with-me` | List todos shared with the current user | Yes |
| GET | `/api/v1/todos/{todo_id}/shares` | List all users a todo is shared with | Yes (Owner only) |

### Request Body & Validation Schema
**POST `/api/v1/todos/{todo_id}/share`**
```json
{
  "email": "collab@example.com",
  "role": "editor" // must be "viewer" or "editor"
}
```

### Responses & Error Codes
- **200 OK**: Successfully shared or role updated.
- **204 No Content**: Successfully revoked access.
- **400 Bad Request**: Attempting to share with oneself.
- **403 Forbidden**: User is not the owner of the todo.
- **404 Not Found**: Todo does not exist, or target email is not registered.

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix
| Action | Owner | Editor | Viewer | Unrelated User |
|---|---|---|---|---|
| GET Todo | Yes | Yes | Yes | No (403) |
| PUT Todo | Yes | Yes | No (403) | No (403) |
| DELETE Todo | Yes | No (403) | No (403) | No (403) |
| Share/Revoke | Yes | No (403) | No (403) | No (403) |

### Edge Cases & Race Conditions
- **Self-sharing prevention**: The API must validate `target_user.id != current_user.id`.
- **Revoke during concurrent update**: If the Owner revokes access while an Editor is typing, the Editor's next `PUT` request will immediately fail with `403 Forbidden` because permissions are checked on every mutation.
- **Duplicate shares**: Handled by the unique constraint and an `ON CONFLICT (todo_id, user_id) DO UPDATE SET role = EXCLUDED.role` upsert logic.

## 7. Caching & Invalidation Strategy
- **List Cache Keys**: 
  - Owner's list: `todos:list:{owner_id}:{page}:{size}`
  - Shared list: `todos:shared:{user_id}:{page}:{size}`
- **Cache Invalidation**:
  - When an Owner creates/updates/deletes a todo, invalidate `todos:list:{owner_id}:*` AND `todos:shared:{collaborator_id}:*` for all associated collaborators.
  - When a Todo is shared or revoked, invalidate `todos:shared:{target_user_id}:*`.
  - When an Editor updates a shared todo, invalidate `todos:shared:{editor_id}:*`, `todos:list:{owner_id}:*`, and any other collaborators' caches.
- **Single Item Cache** (if implemented):
  - `todo:item:{todo_id}` should be invalidated on any update or permission change.
