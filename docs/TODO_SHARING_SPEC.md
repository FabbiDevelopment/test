# Technical Specification: Todo List Sharing

## 1. Overview

### Objective

Cho phép một người dùng (Owner) chia sẻ toàn bộ Todo list của mình cho một người dùng đã đăng ký khác với một trong hai quyền:

- `viewer`: chỉ được xem.
- `editor`: được xem và cập nhật Todo.

Owner có thể thay đổi hoặc thu hồi quyền bất cứ lúc nào. Việc chia sẻ áp dụng cho toàn bộ Todo hiện tại và Todo được tạo sau này của Owner.

### Roles

- **Owner**: chủ sở hữu Todo list và các Todo trong list.
- **Viewer**: người được chia sẻ quyền đọc.
- **Editor**: người được chia sẻ quyền đọc và cập nhật nội dung/trạng thái.

## 2. User stories and acceptance criteria

### US-01 — Owner shares a Todo list

**As an** Owner, **I want to** chia sẻ Todo list bằng email, **so that** một người dùng khác có thể cộng tác.

Acceptance criteria:

- Owner chọn đúng một quyền `viewer` hoặc `editor`.
- Người nhận phải là tài khoản đã đăng ký.
- Owner không thể chia sẻ cho chính mình.
- Mỗi cặp Owner–người nhận chỉ có tối đa một quyền đang hoạt động.
- Chia sẻ thành công trả về grant đã tạo và có hiệu lực ngay.
- Chỉ Owner có thể tạo grant cho list của mình.

### US-02 — Collaborator views a shared Todo list

**As a** Viewer hoặc Editor, **I want to** xem list được chia sẻ, **so that** tôi có thể theo dõi công việc của Owner.

Acceptance criteria:

- Collaborator xem được title, description, completed và timestamps của Todo.
- Kết quả chỉ bao gồm list mà collaborator đang có quyền.
- Response xác định Owner và permission hiện tại.
- Sau khi quyền bị thu hồi, request tiếp theo trả `404` và không trả dữ liệu cache cũ.
- Collaborator không thể đọc list bằng cách đoán `owner_id` nếu không có grant.

### US-03 — Editor updates a Todo

**As an** Editor, **I want to** cập nhật Todo trong shared list, **so that** tôi có thể hỗ trợ Owner quản lý công việc.

Acceptance criteria:

- Editor có thể cập nhật `title`, `description` và `completed`.
- Partial update không làm mất field không được gửi.
- Editor không thể tạo, xóa Todo, chia sẻ tiếp hoặc quản lý quyền.
- Update yêu cầu version hiện tại; version cũ bị từ chối bằng HTTP `409`.
- Update thành công tăng `version` và invalidate cache của Owner cùng mọi collaborator.

### US-04 — Viewer is read-only

**As a** Viewer, **I want to** chỉ xem dữ liệu, **so that** Owner kiểm soát được thay đổi.

Acceptance criteria:

- Viewer có thể list và đọc chi tiết Todo.
- Mọi create, update, delete hoặc permission mutation của Viewer bị từ chối.
- API trả `403` khi Viewer đã có quyền đọc nhưng thiếu quyền thực hiện action.

### US-05 — Owner revokes access

**As an** Owner, **I want to** thu hồi quyền, **so that** collaborator không thể tiếp tục truy cập.

Acceptance criteria:

- Chỉ Owner có thể revoke grant.
- Revoke là idempotent ở mức client: grant không tồn tại được trả `404`, không làm thay đổi grant khác.
- Sau khi transaction revoke commit, request mới của collaborator không thể đọc hoặc sửa list.
- Cache liên quan đến collaborator bị invalidate đồng bộ.
- Owner và các grant còn lại vẫn truy cập bình thường.

## 3. Scope

### In scope

- Chia sẻ toàn bộ Todo list cho một tài khoản đã đăng ký.
- Quyền Viewer và Editor.
- Liệt kê, thay đổi và thu hồi quyền bởi Owner.
- Đọc shared list và Editor cập nhật Todo.
- Optimistic concurrency cho Todo update.
- Audit timestamps và cache invalidation.

### Out of scope

- Chia sẻ từng Todo riêng lẻ.
- Lời mời qua email cho người chưa đăng ký hoặc pending invitation workflow.
- Link chia sẻ công khai, anonymous access hoặc password-protected link.
- Editor tạo/xóa Todo, chia sẻ tiếp hoặc cấp quyền cho người khác.
- Nhiều role tùy chỉnh ngoài Viewer/Editor.
- Notification, email, activity feed và audit-log UI.
- Realtime collaboration qua WebSocket.
- Chuyển quyền sở hữu Todo list.
- Khôi phục grant đã revoke; Owner tạo grant mới nếu muốn chia sẻ lại.

## 4. Data model

### 4.1 New table: `todo_shares`

| Field | Type | Null | Description |
|---|---|---:|---|
| `id` | UUID | No | Primary key, generated server-side |
| `owner_id` | UUID | No | FK đến `users.id`; chủ Todo list |
| `grantee_id` | UUID | No | FK đến `users.id`; người được chia sẻ |
| `permission` | VARCHAR(10) | No | `viewer` hoặc `editor` |
| `created_at` | TIMESTAMPTZ | No | Thời điểm cấp quyền |
| `updated_at` | TIMESTAMPTZ | No | Thời điểm thay đổi quyền gần nhất |

Constraints:

- Primary key: `todo_shares.id`.
- Unique constraint: `UNIQUE (owner_id, grantee_id)` chống duplicate grant và race condition.
- Check constraint: `permission IN ('viewer', 'editor')`.
- Check constraint: `owner_id <> grantee_id` chống self-sharing ở tầng database.
- `owner_id REFERENCES users(id) ON DELETE CASCADE`.
- `grantee_id REFERENCES users(id) ON DELETE CASCADE`.

Indexes:

- Unique index của `(owner_id, grantee_id)` phục vụ kiểm tra quyền theo cặp.
- `INDEX todo_shares_grantee_id_idx (grantee_id)` phục vụ danh sách được chia sẻ với user.
- Không tạo index đơn lẻ cho `owner_id` vì prefix của unique index đã phục vụ truy vấn này.

Khi một user bị xóa, các grant mà user là Owner hoặc collaborator đều bị xóa tự động. Todo vẫn tuân theo lifecycle hiện tại của Owner; migration triển khai tính năng này cũng cần chuẩn hóa `todos.user_id` thành `ON DELETE CASCADE` nếu product quyết định xóa user đồng thời xóa Todo.

### 4.2 Altered table: `todos`

Thêm field:

| Field | Type | Null | Default | Description |
|---|---|---:|---:|---|
| `version` | INTEGER | No | `1` | Optimistic concurrency token |

Mỗi update hợp lệ thực hiện nguyên tử `version = version + 1`. Không chấp nhận giá trị nhỏ hơn 1.

### 4.3 Permission matrix

| Action | Owner | Editor | Viewer | No grant |
|---|:---:|:---:|:---:|:---:|
| List/read Todo | Yes | Yes | Yes | No |
| Create Todo | Yes | No | No | No |
| Update Todo | Yes | Yes | No | No |
| Delete Todo | Yes | No | No | No |
| List/manage grants | Yes | No | No | No |
| Re-share list | Yes | No | No | No |

## 5. API design

Tất cả endpoint yêu cầu Bearer access token. UUID không hợp lệ trả `422`. Resource không tồn tại hoặc caller không được biết resource tồn tại trả `404` để hạn chế enumeration.

### 5.1 Endpoint summary

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/todo-shares` | Owner cấp quyền |
| `GET` | `/api/v1/todo-shares` | Owner liệt kê grant đã cấp |
| `PATCH` | `/api/v1/todo-shares/{share_id}` | Owner đổi Viewer/Editor |
| `DELETE` | `/api/v1/todo-shares/{share_id}` | Owner thu hồi quyền |
| `GET` | `/api/v1/shared-todo-lists` | Liệt kê list được share cho caller |
| `GET` | `/api/v1/shared-todo-lists/{owner_id}/todos` | Đọc Todo trong shared list |
| `GET` | `/api/v1/shared-todo-lists/{owner_id}/todos/{todo_id}` | Đọc một shared Todo |
| `PATCH` | `/api/v1/shared-todo-lists/{owner_id}/todos/{todo_id}` | Editor cập nhật Todo |

### 5.2 Create a share

`POST /api/v1/todo-shares`

Request:

```json
{
  "grantee_email": "collaborator@example.com",
  "permission": "editor"
}
```

Response `201 Created`:

```json
{
  "id": "3d88d2b4-37e3-4a38-a3a7-5c7084aa11ad",
  "owner_id": "43cf27d8-a1b3-4ce6-9bcb-91e9118fac31",
  "grantee": {
    "id": "9de47d86-65ef-4d68-85bc-e2b311392ae3",
    "email": "collaborator@example.com"
  },
  "permission": "editor",
  "created_at": "2026-09-17T10:00:00Z",
  "updated_at": "2026-09-17T10:00:00Z"
}
```

Errors: `400 SELF_SHARE_NOT_ALLOWED`, `404 USER_NOT_FOUND`, `409 SHARE_ALREADY_EXISTS`, `422 VALIDATION_ERROR`.

### 5.3 List grants created by Owner

`GET /api/v1/todo-shares?page=1&size=20`

Response `200 OK`:

```json
{
  "items": [
    {
      "id": "3d88d2b4-37e3-4a38-a3a7-5c7084aa11ad",
      "grantee": {
        "id": "9de47d86-65ef-4d68-85bc-e2b311392ae3",
        "email": "collaborator@example.com"
      },
      "permission": "editor",
      "created_at": "2026-09-17T10:00:00Z",
      "updated_at": "2026-09-17T10:00:00Z"
    }
  ],
  "page": 1,
  "size": 20,
  "total": 1
}
```

### 5.4 Change permission

`PATCH /api/v1/todo-shares/{share_id}`

Request:

```json
{
  "permission": "viewer"
}
```

Response: `200 OK` với share object đã cập nhật. Errors: `404 SHARE_NOT_FOUND`, `422 VALIDATION_ERROR`.

### 5.5 Revoke permission

`DELETE /api/v1/todo-shares/{share_id}`

Response: `204 No Content`. Errors: `404 SHARE_NOT_FOUND`.

### 5.6 List shared Todo lists

`GET /api/v1/shared-todo-lists?page=1&size=20`

Response `200 OK`:

```json
{
  "items": [
    {
      "owner": {
        "id": "43cf27d8-a1b3-4ce6-9bcb-91e9118fac31",
        "email": "owner@example.com"
      },
      "permission": "viewer",
      "todo_count": 12
    }
  ],
  "page": 1,
  "size": 20,
  "total": 1
}
```

### 5.7 Read shared Todos

`GET /api/v1/shared-todo-lists/{owner_id}/todos?page=1&size=20`

Response `200 OK` dùng cấu trúc Todo list hiện tại và bổ sung `owner_id`, `permission`. Errors: `404 SHARED_LIST_NOT_FOUND`.

### 5.8 Update a shared Todo

`PATCH /api/v1/shared-todo-lists/{owner_id}/todos/{todo_id}`

Request:

```json
{
  "title": "Updated by editor",
  "completed": true,
  "version": 4
}
```

Response `200 OK`:

```json
{
  "id": "17a0f433-20ca-44ca-b910-d0b60746b3ed",
  "title": "Updated by editor",
  "description": "Existing description is preserved",
  "completed": true,
  "owner_id": "43cf27d8-a1b3-4ce6-9bcb-91e9118fac31",
  "version": 5,
  "updated_at": "2026-09-17T10:05:00Z"
}
```

Errors: `403 INSUFFICIENT_PERMISSION`, `404 TODO_NOT_FOUND`, `409 VERSION_CONFLICT`, `422 VALIDATION_ERROR`.

### 5.9 Standard error payload

```json
{
  "error": {
    "code": "VERSION_CONFLICT",
    "message": "The todo was updated by another user.",
    "details": {
      "current_version": 5
    },
    "request_id": "req_01J7XYZ"
  }
}
```

| Status | Meaning |
|---:|---|
| `400` | Business rule vi phạm, ví dụ tự share |
| `401` | Thiếu, hết hạn hoặc sai access token |
| `403` | Đã nhìn thấy resource nhưng role không cho phép action |
| `404` | User/share/Todo không tồn tại hoặc caller không được biết resource |
| `409` | Duplicate share hoặc optimistic concurrency conflict |
| `422` | Request schema không hợp lệ |
| `503` | Dependency bắt buộc không khả dụng và không thể bảo đảm consistency |

## 6. Authorization and edge cases

### Self-sharing

- Service so sánh `current_user.id` với `grantee.id` trước khi insert.
- Database check constraint là lớp bảo vệ cuối cùng.
- Trả `400 SELF_SHARE_NOT_ALLOWED`.

### Duplicate invite and concurrent create

- Service kiểm tra grant hiện có để trả lỗi thân thiện.
- `UNIQUE (owner_id, grantee_id)` là nguồn bảo đảm khi hai request chạy đồng thời.
- Bắt unique-violation và chuyển thành `409 SHARE_ALREADY_EXISTS`.
- Thay đổi Viewer sang Editor phải dùng `PATCH`, không tạo grant thứ hai.

### Concurrent Todo update

Update dùng optimistic locking:

```sql
UPDATE todos
SET title = :title,
    version = version + 1,
    updated_at = now()
WHERE id = :todo_id
  AND user_id = :owner_id
  AND version = :expected_version;
```

Nếu affected-row count bằng 0, service đọc lại resource: trả `404` nếu không tồn tại hoặc `409 VERSION_CONFLICT` nếu version đã thay đổi. Client phải reload rồi cho người dùng quyết định áp dụng lại thay đổi.

### Revoke racing with Editor update

- Editor update kiểm tra grant trong cùng database transaction và khóa grant bằng `SELECT ... FOR SHARE`.
- Revoke khóa cùng grant bằng `SELECT ... FOR UPDATE`, sau đó xóa và commit.
- Nếu update giữ lock trước, update hoàn tất trước revoke. Nếu revoke commit trước, update không còn tìm thấy grant và bị từ chối.
- Sau thời điểm revoke commit, không có update mới nào được phép thành công.

### Information disclosure

- Đoán `owner_id`, `share_id` hoặc `todo_id` không được làm lộ resource của user khác.
- Endpoint đọc trả `404` khi không có grant.
- Viewer update trả `403` vì Viewer đã được phép biết Todo tồn tại nhưng thiếu action permission.
- Log nội bộ có thể ghi reason thật nhưng response không chứa thông tin nhạy cảm.

## 7. Cache and invalidation

Authorization không được quyết định chỉ dựa trên Todo response cache. Mỗi shared-list request phải xác nhận grant còn tồn tại trong database trước khi đọc cached response; nhờ đó cached data không thể tiếp tục cấp quyền sau revoke.

Suggested keys:

```text
shared-lists:{grantee_id}:page:{page}:size:{size}
shared-todos:{grantee_id}:owner:{owner_id}:page:{page}:size:{size}
owner-todos:{owner_id}:page:{page}:size:{size}
```

Invalidation rules:

- Create grant: xóa `shared-lists:{grantee_id}:*`.
- Change permission: xóa `shared-lists:{grantee_id}:*` và `shared-todos:{grantee_id}:owner:{owner_id}:*`.
- Revoke: commit database trước, sau đó đồng bộ xóa hai nhóm key của grantee trước khi trả response.
- Todo create/update/delete: xóa cache list của Owner và mọi grantee đang active.
- Nếu cache invalidation sau revoke thất bại, authorization database vẫn fail closed; enqueue retry/metric và không phục vụ cached data cho request không còn grant.

Không dùng Redis `KEYS` trên production. Dùng versioned namespace hoặc `SCAN`/tracked cache keys để tránh block Redis.

## 8. Observability and testing

- Audit log có `actor_id`, `owner_id`, `grantee_id`, `share_id`, action và request ID; không log JWT.
- Metrics: create/revoke count, authorization denied count, version conflict count và cache invalidation failure count.
- Integration tests bắt buộc: self-share, duplicate concurrent share, Viewer update denied, Editor update allowed, cross-user ID guessing, version conflict và immediate revoke.
- E2E: Owner share → Viewer reads; Owner upgrades to Editor → update succeeds; Owner revokes → access disappears.

## 9. Rollout and migration

1. Deploy additive migration tạo `todo_shares` và nullable/defaulted `todos.version` theo chiến lược phù hợp với phiên bản PostgreSQL.
2. Backfill `version = 1` theo batch nếu cần, sau đó đặt `NOT NULL`.
3. Deploy API đọc/ghi schema mới nhưng giữ feature flag tắt.
4. Bật feature theo phần trăm người dùng và theo dõi authorization/cache metrics.
5. Rollback application bằng feature flag; không drop table/column trong cùng release để tránh mất dữ liệu.
