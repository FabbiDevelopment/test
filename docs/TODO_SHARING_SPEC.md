# Technical Specification: Todo List Sharing & Collaboration System

> **Status:** Draft / Specification Phase  
> **Author:** Jackie Luong  
> **Target Release:** Tier 3 Core Enhancement  

---

## 1. Overview & Objective

### 1.1 Feature Summary
The **Todo List Sharing System** enables users (Owners) to share access to their todo items with other registered users in the application. Collaborators can be assigned explicit roles: **Viewer** (read-only access) or **Editor** (read, create, update, and toggle access). Owners retain full administrative control and can modify permissions or revoke access at any time.

### 1.2 Problem Statement
Currently, todos are strictly isolated to individual user accounts (as fixed in Tier 1 Bug #2 and Bug #3). Users cannot collaborate on shared tasks, projects, or household checklists. This feature introduces secure, multi-tenant collaboration while strictly preserving cross-user data boundaries.

### 1.3 Target Audience & Roles
- **Owner:** The user who created the todo items. Possesses full CRUD administrative rights and sole authority to grant or revoke share access.
- **Editor (Collaborator):** A user granted read, create, edit, and toggle privileges over the owner's todo list. Cannot delete the list or manage share permissions.
- **Viewer (Collaborator):** A user granted read-only privileges over the owner's todo list. Cannot create, edit, toggle, or delete any todos.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Share Todo List with Collaborator (Owner Flow)
- **As an** Owner
- **I want to** share my todo list with another user by specifying their email address and permission level (`viewer` or `editor`)
- **So that** we can collaborate on tasks together
- **Acceptance Criteria:**
  - [ ] Owner can invite a user via valid email address.
  - [ ] System verifies the recipient email exists in the system.
  - [ ] System prevents self-sharing (Owner entering their own email).
  - [ ] System prevents duplicate share invites to the same user (returns `400 Bad Request`).
  - [ ] A new share record is created with default `viewer` or specified `editor` permission.

### User Story 2: Access & Edit Shared Todos (Collaborator Flow)
- **As a** Collaborator (Viewer / Editor)
- **I want to** view or modify shared todos according to my assigned permission level
- **So that** I can track progress or complete assigned tasks
- **Acceptance Criteria:**
  - [ ] Viewers can fetch shared todos (`GET /api/v1/todos/shared`), but mutation attempts (`POST`, `PUT`, `DELETE`) return `403 Forbidden`.
  - [ ] Editors can create, update, or toggle completion of shared todos.
  - [ ] Editors cannot delete the owner's original todo items or manage list share permissions.

### User Story 3: Revoke Access (Owner Flow)
- **As an** Owner
- **I want to** list active share permissions and revoke access from any collaborator at any time
- **So that** I can maintain security when collaboration is completed
- **Acceptance Criteria:**
  - [ ] Owner can view all users who currently have shared access to their list.
  - [ ] Owner can send a `DELETE /api/v1/shares/{share_id}` request to revoke access immediately.
  - [ ] Revocation instantly invalidates collaborator Redis caches; subsequent collaborator requests return `403 Forbidden`.

---

## 3. Scope

### In-Scope
- User-level todo list sharing (Owner shares their todo collection with Collaborators).
- Role-based Access Control (RBAC): `viewer` vs `editor`.
- Endpoint to grant, list, update, and revoke share access.
- Immediate Redis cache invalidation upon share permission revocation.

### Out-of-Scope (Future Iterations)
- Fine-grained item-level ACL (sharing an individual todo ID rather than the collection).
- Public link sharing without authentication.
- Real-time WebSocket notifications for collaborative edits.

---

## 4. Database Design

### 4.1 Proposed Schema: `user_shares` Table

```sql
CREATE TYPE share_permission_enum AS ENUM ('viewer', 'editor');

CREATE TABLE user_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    permission share_permission_enum NOT NULL DEFAULT 'viewer',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_owner_shared_user UNIQUE (owner_id, shared_with_user_id),
    CONSTRAINT chk_no_self_share CHECK (owner_id <> shared_with_user_id)
);

-- Indexes for performance
CREATE INDEX idx_user_shares_owner ON user_shares(owner_id);
CREATE INDEX idx_user_shares_shared_with ON user_shares(shared_with_user_id);
```

### 4.2 Data Integrity Rules
- **Foreign Keys:** References `users.id`. `ON DELETE CASCADE` ensures that if an owner or collaborator account is deleted, all associated share records are automatically purged.
- **Unique Constraint:** `uq_owner_shared_user (owner_id, shared_with_user_id)` enforces a single active share relationship per user pair.
- **Check Constraint:** `chk_no_self_share` prevents database insertion if `owner_id = shared_with_user_id`.

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/shares` | Grant or update share permission to a user | Yes (Owner) |
| GET | `/api/v1/shares` | List all users with shared access to Owner's list | Yes (Owner) |
| DELETE | `/api/v1/shares/{share_id}` | Revoke shared access from a collaborator | Yes (Owner) |
| GET | `/api/v1/todos/shared` | List todos shared with the current user | Yes (Collaborator) |

### 5.1 Request & Response Schemas

#### Grant Share Access: `POST /api/v1/shares`
```json
// Request Body
{
  "email": "collaborator@example.com",
  "permission": "editor"
}

// Response (201 Created)
{
  "id": "e8b7a6c5-d4e3-4f2a-1b0c-9d8e7f6a5b4c",
  "owner_id": "0ce2f600-5b81-4435-bd93-ee4fd9b9c86b",
  "shared_with_user_id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "shared_with_email": "collaborator@example.com",
  "permission": "editor",
  "created_at": "2026-09-19T16:00:00Z"
}
```

#### Error Response Payloads
- `400 Bad Request` (Self-sharing or duplicate invite):
  ```json
  { "detail": "Cannot share todo list with yourself" }
  ```
- `404 Not Found` (Target user email does not exist):
  ```json
  { "detail": "User with this email was not found" }
  ```
- `403 Forbidden` (Collaborator attempting unauthorized action):
  ```json
  { "detail": "You have read-only (viewer) access to this todo list" }
  ```

---

## 6. Business Logic & Security Considerations

### 6.1 Permission Matrix

| Role | Read Todos | Create Todo | Update Todo | Delete Todo | Manage Shares |
|---|:---:|:---:|:---:|:---:|:---:|
| **Owner** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Editor** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **Viewer** | ✅ | ❌ | ❌ | ❌ | ❌ |

### 6.2 Edge Cases & Race Conditions
1. **Self-Sharing Attempt:** Backend validates `request.email != current_user.email` before database query.
2. **Duplicate Invites:** DB unique constraint `uq_owner_shared_user` catches race conditions; application returns HTTP 400.
3. **Concurrent Revocation:** If Owner revokes access while Collaborator is submitting an edit:
   - Dependency check `get_current_share_permission()` checks DB/Redis.
   - If share record is missing, request immediately aborts with `HTTP 403 Forbidden`.

---

## 7. Caching & Invalidation Strategy

### 7.1 Redis Cache Key Structure
- Shared todo list query cache: `todos:shared:{collaborator_id}:{owner_id}`
- Active permission cache: `permissions:{owner_id}:{collaborator_id}` (TTL = 1 hour)

### 7.2 Invalidation Events
1. **Permission Revocation (`DELETE /api/v1/shares/{id}`):**
   - Invalidate `permissions:{owner_id}:{collaborator_id}`
   - Invalidate `todos:shared:{collaborator_id}:*`
2. **Collaborator / Owner Mutations (`POST/PUT /todos`):**
   - Invalidate Owner's cache `todos:list:{owner_id}:*`
   - Invalidate all active collaborators' shared caches `todos:shared:*:{owner_id}` using Redis `SCAN + DEL`.
