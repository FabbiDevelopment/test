# Technical Specification: Todo Sharing

> Đặc tả kỹ thuật cho tính năng chia sẻ danh sách Todo giữa các người dùng.

## 1. Overview & Objective

- **Feature Summary**: Cho phép chủ sở hữu (Owner) chia sẻ danh sách Todo của mình cho người dùng khác trong hệ thống với quyền chỉ đọc (Viewer) hoặc quyền chỉnh sửa (Editor). Owner có thể thu hồi quyền truy cập bất kỳ lúc nào.
- **Problem Statement**: Hiện tại mỗi người dùng chỉ có thể xem và quản lý Todo của riêng mình, không có cơ chế cộng tác. Trong môi trường làm việc nhóm, các thành viên cần theo dõi và phối hợp công việc chung.
- **Target Audience / Roles**:
  - **Owner**: Người tạo ra Todo, có toàn quyền CRUD và quản lý chia sẻ.
  - **Editor**: Người được chia sẻ quyền chỉnh sửa, có thể xem và cập nhật Todo (title, description, completed) nhưng không thể xóa hoặc chia sẻ tiếp.
  - **Viewer**: Người được chia sẻ quyền chỉ đọc, chỉ có thể xem Todo mà không thể thay đổi bất kỳ thông tin nào.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ Todo cho người dùng khác
- **As a** Todo Owner
- **I want to** chia sẻ danh sách Todo của mình cho một người dùng khác bằng email
- **So that** họ có thể xem hoặc cùng chỉnh sửa công việc với tôi
- **Acceptance Criteria**:
  - [ ] Owner nhập email người nhận và chọn quyền (viewer / editor).
  - [ ] Hệ thống xác nhận email tồn tại trong hệ thống trước khi tạo lời mời.
  - [ ] Nếu email không tồn tại, trả về lỗi 404 với thông báo "User not found".
  - [ ] Nếu đã chia sẻ trước đó cho cùng email, trả về lỗi 409 Conflict.
  - [ ] Người được chia sẻ có thể thấy Todo ngay sau khi lời mời được tạo.

### User Story 2: Xem danh sách Todo được chia sẻ cho tôi
- **As a** Viewer hoặc Editor
- **I want to** xem danh sách các Todo mà người khác đã chia sẻ cho tôi
- **So that** tôi có thể theo dõi và phối hợp công việc
- **Acceptance Criteria**:
  - [ ] API trả về danh sách Todo được chia sẻ, tách biệt với Todo cá nhân.
  - [ ] Mỗi Todo hiển thị kèm tên/email của Owner và quyền hiện tại (viewer/editor).

### User Story 3: Chỉnh sửa Todo được chia sẻ (Editor)
- **As an** Editor
- **I want to** cập nhật title, description, hoặc completed status của Todo được chia sẻ
- **So that** tôi có thể cộng tác hiệu quả với Owner
- **Acceptance Criteria**:
  - [ ] Editor có thể gọi PUT /todos/{id} để cập nhật Todo.
  - [ ] Viewer gọi PUT /todos/{id} bị từ chối với HTTP 403 Forbidden.
  - [ ] Editor không thể xóa Todo (chỉ Owner mới được xóa).

### User Story 4: Thu hồi quyền truy cập
- **As a** Todo Owner
- **I want to** thu hồi quyền truy cập của một người dùng đã được chia sẻ
- **So that** họ không còn xem hoặc chỉnh sửa Todo của tôi nữa
- **Acceptance Criteria**:
  - [ ] Owner gọi DELETE để xóa bản ghi chia sẻ.
  - [ ] Người bị thu hồi mất quyền truy cập ngay lập tức.
  - [ ] Cache Redis liên quan đến người bị thu hồi được xóa ngay lập tức.

### User Story 5: Cập nhật quyền chia sẻ
- **As a** Todo Owner
- **I want to** thay đổi quyền của người được chia sẻ từ Viewer sang Editor hoặc ngược lại
- **So that** tôi có thể linh hoạt quản lý mức độ truy cập
- **Acceptance Criteria**:
  - [ ] Owner gọi PATCH để cập nhật trường `permission` (viewer ↔ editor).
  - [ ] Quyền mới có hiệu lực ngay lập tức ở request tiếp theo.

---

## 3. Scope

### In-Scope (Phiên bản này)
- Chia sẻ Todo theo đơn vị từng todo item (không phải toàn bộ danh sách).
- Hai mức quyền: `viewer` (chỉ đọc) và `editor` (đọc + sửa).
- Owner quản lý chia sẻ (tạo, cập nhật quyền, thu hồi).
- API endpoint RESTful đầy đủ cho CRUD sharing.
- Xóa cache Redis ngay khi thay đổi quyền.

### Out-of-Scope (Phiên bản sau)
- Chia sẻ bằng link công khai (public link sharing).
- Hệ thống thông báo realtime (WebSocket / Push Notification) khi được chia sẻ.
- Chuyển quyền sở hữu (transfer ownership) cho người khác.
- Chia sẻ cấp thư mục / nhóm Todo (folder-level sharing).
- Người được chia sẻ tiếp tục chia sẻ cho người thứ ba (re-sharing / delegation).
- Lịch sử hoạt động / audit log (ai đã sửa gì, khi nào).

---

## 4. Database Design

### Bảng mới: `todo_shares`

| Column | Type | Constraints | Description |
|---|---|---|---|
| `id` | `UUID` | PRIMARY KEY, DEFAULT uuid4 | ID bản ghi chia sẻ |
| `todo_id` | `UUID` | FOREIGN KEY → `todos.id` ON DELETE CASCADE, NOT NULL | Todo được chia sẻ |
| `owner_id` | `UUID` | FOREIGN KEY → `users.id` ON DELETE CASCADE, NOT NULL | Người sở hữu Todo (denormalized để tối ưu truy vấn) |
| `shared_with_id` | `UUID` | FOREIGN KEY → `users.id` ON DELETE CASCADE, NOT NULL | Người được chia sẻ |
| `permission` | `VARCHAR(10)` | NOT NULL, CHECK IN ('viewer', 'editor') | Mức quyền truy cập |
| `created_at` | `TIMESTAMPTZ` | NOT NULL, DEFAULT now() | Thời điểm tạo chia sẻ |

### Constraints & Indexes

```sql
-- Ngăn chặn chia sẻ trùng lặp (cùng todo + cùng người nhận)
UNIQUE (todo_id, shared_with_id)

-- Tối ưu truy vấn: Danh sách todo được chia sẻ cho tôi
INDEX idx_todo_shares_shared_with_id ON todo_shares (shared_with_id)

-- Tối ưu truy vấn: Owner xem ai đang được chia sẻ todo này
INDEX idx_todo_shares_todo_id ON todo_shares (todo_id)

-- Cascade delete: Khi xóa Todo → Tự động xóa tất cả bản ghi chia sẻ liên quan
-- Khi xóa User → Tự động xóa tất cả bản ghi chia sẻ mà user đó là owner hoặc là người nhận
```

### Mô hình quan hệ (ERD)

```
┌─────────┐       ┌──────────────┐       ┌─────────┐
│  users  │──1:N──│ todo_shares  │──N:1──│  todos  │
│         │       │              │       │         │
│  id     │       │  id          │       │  id     │
│  email  │       │  todo_id  ──────FK───│         │
│         │◀──FK──│  owner_id    │       │  title  │
│         │◀──FK──│  shared_with │       │  ...    │
│         │       │  permission  │       │  user_id│
└─────────┘       │  created_at  │       └─────────┘
                  └──────────────┘
```

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todos/{todo_id}/shares` | Chia sẻ todo cho user khác | Yes (Owner only) |
| GET | `/api/v1/todos/{todo_id}/shares` | Xem danh sách người được chia sẻ | Yes (Owner only) |
| PATCH | `/api/v1/todos/{todo_id}/shares/{share_id}` | Cập nhật quyền (viewer ↔ editor) | Yes (Owner only) |
| DELETE | `/api/v1/todos/{todo_id}/shares/{share_id}` | Thu hồi quyền chia sẻ | Yes (Owner only) |
| GET | `/api/v1/todos/shared-with-me` | Danh sách todo được chia sẻ cho tôi | Yes |

### Request / Response Examples

#### POST `/api/v1/todos/{todo_id}/shares` — Tạo chia sẻ
**Request Body:**
```json
{
  "email": "collaborator@example.com",
  "permission": "editor"
}
```
**Validation:**
- `email`: Required, phải là email hợp lệ.
- `permission`: Required, chỉ chấp nhận `"viewer"` hoặc `"editor"`.

**Success Response (201 Created):**
```json
{
  "id": "share-uuid-...",
  "todo_id": "todo-uuid-...",
  "shared_with": {
    "id": "user-uuid-...",
    "email": "collaborator@example.com"
  },
  "permission": "editor",
  "created_at": "2026-10-07T12:00:00Z"
}
```

**Error Responses:**

| Status | Condition | Response Body |
|---|---|---|
| 400 | Owner tự share cho chính mình | `{"detail": "Cannot share todo with yourself"}` |
| 404 | Todo không tồn tại hoặc không phải Owner | `{"detail": "Todo not found"}` |
| 404 | Email người nhận không tồn tại | `{"detail": "User not found"}` |
| 409 | Đã chia sẻ cho email này rồi | `{"detail": "Todo already shared with this user"}` |

#### GET `/api/v1/todos/shared-with-me` — Danh sách todo được chia sẻ cho tôi
**Success Response (200 OK):**
```json
{
  "items": [
    {
      "id": "todo-uuid-...",
      "title": "Team Sprint Plan",
      "description": "Plan for Q4",
      "completed": false,
      "owner_email": "leader@example.com",
      "permission": "editor",
      "created_at": "2026-10-01T08:00:00Z"
    }
  ],
  "total": 1
}
```

---

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Action | Owner | Editor | Viewer | Unauthenticated |
|---|---|---|---|---|
| Xem Todo | ✅ | ✅ | ✅ | ❌ |
| Sửa Todo (title, description, completed) | ✅ | ✅ | ❌ (403) | ❌ |
| Xóa Todo | ✅ | ❌ (403) | ❌ (403) | ❌ |
| Chia sẻ Todo | ✅ | ❌ (403) | ❌ (403) | ❌ |
| Thu hồi quyền | ✅ | ❌ (403) | ❌ (403) | ❌ |

### Edge Cases & Race Conditions

| Edge Case | Cách xử lý |
|---|---|
| **Owner tự share cho chính mình** | API từ chối ngay lập tức: HTTP 400 `"Cannot share todo with yourself"`. Kiểm tra `shared_with_id != current_user.id` trước khi insert. |
| **Mời trùng lặp (Duplicate invite)** | Ràng buộc UNIQUE `(todo_id, shared_with_id)` ở tầng Database. API bắt `IntegrityError` và trả về HTTP 409 Conflict. |
| **Owner thu hồi quyền trong lúc Editor đang gửi request sửa** | Hàm `get_current_user_permission()` kiểm tra quyền realtime từ DB tại mỗi request. Sau khi Owner xóa bản ghi `todo_shares`, request tiếp theo của Editor sẽ bị từ chối HTTP 403 ngay lập tức. |
| **Owner xóa Todo trong khi Collaborator đang xem** | Cascade delete: Xóa Todo tự động xóa tất cả bản ghi `todo_shares` liên quan. Request tiếp theo của Collaborator trả về HTTP 404. |
| **Người được chia sẻ bị xóa tài khoản** | Cascade delete trên FK `shared_with_id → users.id`: Tự động dọn dẹp tất cả bản ghi share. |
| **Concurrent update: 2 Editor cùng sửa 1 Todo** | Sử dụng cơ chế "last write wins" (mặc định). Nếu cần strict consistency, có thể bổ sung Optimistic Locking bằng cột `version` (out-of-scope phiên bản này). |

---

## 7. Caching & Invalidation Strategy

### Cấu trúc Redis Cache Key

```
# Danh sách Todo cá nhân (đã có)
todos:list:{user_id}:{page}:{size}

# Danh sách Todo được chia sẻ cho tôi (mới)
todos:shared:{shared_with_id}:{page}:{size}

# Danh sách người được chia sẻ của 1 todo (mới)
todos:shares:{todo_id}
```

### Thời điểm cần Invalidate Cache

| Sự kiện | Cache keys cần xóa |
|---|---|
| Owner tạo share mới | `todos:shared:{shared_with_id}:*` + `todos:shares:{todo_id}` |
| Owner thu hồi quyền | `todos:shared:{shared_with_id}:*` + `todos:shares:{todo_id}` |
| Owner cập nhật quyền | `todos:shared:{shared_with_id}:*` + `todos:shares:{todo_id}` |
| Owner/Editor cập nhật Todo | `todos:list:{owner_id}:*` + `todos:shared:{all_collaborator_ids}:*` |
| Owner xóa Todo | `todos:list:{owner_id}:*` + `todos:shared:{all_collaborator_ids}:*` + `todos:shares:{todo_id}` |

> **Nguyên tắc bảo mật**: Khi Owner thu hồi quyền, cache của người bị thu hồi **phải** được xóa ngay lập tức (không chờ TTL hết hạn), đảm bảo người bị thu hồi không thể nhìn thấy dữ liệu cũ từ cache.
