# Technical Specification: Todo Sharing Feature

## 1. Overview & Objective
- **Feature Summary**: Cho phép người dùng sở hữu danh sách Todo (Owner) chia sẻ toàn bộ hoặc từng Todo item cụ thể với những người dùng khác trong hệ thống theo các cấp độ phân quyền (Viewer hoặc Editor), và cho phép Owner thu hồi quyền bất kỳ lúc nào.
- **Problem Statement**: Hiện tại các Todo mang tính cá nhân đơn lẻ. Người dùng cần phối hợp công việc theo nhóm hoặc làm việc chung mà không muốn chia sẻ thông tin tài khoản cá nhân.
- **Target Audience / Roles**:
  - **Owner**: Người tạo ra Todo / Sở hữu Todo gốc. Có toàn quyền (CRUD, chia sẻ, thu hồi quyền).
  - **Editor (Collaborator)**: Người được chia sẻ với quyền Chỉnh sửa (Xem, sửa nội dung, toggle completed). Không thể xóa Todo gốc và không được chia sẻ tiếp cho người khác.
  - **Viewer (Guest)**: Người được chia sẻ với quyền Chỉ xem (Read-only). Không thể chỉnh sửa hay xóa.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ Todo cho người dùng khác
- **As an** Owner của một Todo
- **I want to** chia sẻ Todo đó cho một người dùng khác qua Email với quyền `viewer` hoặc `editor`
- **So that** họ có thể theo dõi hoặc cùng thực hiện công việc với tôi.
- **Acceptance Criteria**:
  - [ ] Hệ thống kiểm tra xem email của người nhận có tồn tại trong hệ thống hay không.
  - [ ] Không cho phép Owner tự chia sẻ Todo cho chính mình (gửi về lỗi 400 Bad Request).
  - [ ] Nếu đã chia sẻ trước đó, hệ thống hỗ trợ cập nhật lại role (`viewer` <-> `editor`) thay vì báo lỗi trùng lặp.
  - [ ] Ngay khi chia sẻ thành công, cache danh sách Todo của người được chia sẻ lập tức được vô hiệu hóa để hiển thị Todo mới.

### User Story 2: Thu hồi quyền chia sẻ
- **As an** Owner của một Todo
- **I want to** xóa quyền truy cập của một collaborator đã được chia sẻ
- **So that** họ không còn xem hoặc sửa Todo đó nữa.
- **Acceptance Criteria**:
  - [ ] Chỉ có Owner mới có quyền thu hồi chia sẻ.
  - [ ] Ngay sau khi thu hồi, collaborator thực hiện bất kỳ request nào đến Todo đó sẽ nhận lỗi HTTP 403/404.
  - [ ] Redis cache của collaborator lập tức bị xóa.

---

## 3. Scope
- **In-Scope**:
  - Chia sẻ Todo item cụ thể theo `user_id` người nhận với role `viewer` hoặc `editor`.
  - API liệt kê danh sách những người đang được chia sẻ Todo đó (dành cho Owner).
  - API cập nhật hoặc thu hồi quyền chia sẻ.
  - Tích hợp Phân quyền RBAC & Cache Invalidation trong Redis.
- **Out-of-Scope**:
  - Chia sẻ theo nhóm / Team / Workspace (để dành phiên bản v2).
  - Gửi Email thông báo khi được chia sẻ.
  - Phân quyền theo khoảng thời gian hết hạn (Time-based expiration).

---

## 4. Database Design

### New Table: `todo_shares`

```sql
CREATE TABLE todo_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    todo_id UUID NOT NULL REFERENCES todos(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('viewer', 'editor')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_todo_share UNIQUE (todo_id, shared_with_user_id)
);

CREATE INDEX idx_todo_shares_user_id ON todo_shares(shared_with_user_id);
CREATE INDEX idx_todo_shares_todo_id ON todo_shares(todo_id);
```

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todos/{id}/share` | Chia sẻ Todo với user khác | Yes (Owner) |
| GET | `/api/v1/todos/{id}/shares` | Lấy danh sách users đang được share | Yes (Owner) |
| DELETE | `/api/v1/todos/{id}/share/{user_id}` | Thu hồi quyền chia sẻ | Yes (Owner) |
| GET | `/api/v1/todos/shared-with-me` | Lấy danh sách Todo được chia sẻ với mình | Yes |

### Request Payload: `POST /api/v1/todos/{id}/share`
```json
{
  "email": "collaborator@example.com",
  "role": "editor"
}
```

### Error Payloads:
- `400 Bad Request`: Self-sharing (`"Cannot share todo with yourself"`).
- `403 Forbidden`: Non-owner attempting to share (`"Only the owner can share this todo"`).
- `404 Not Found`: Target user or Todo not found.

---

## 6. Business Logic & Security Considerations

### Authorization Matrix:
| Operation | Owner | Editor | Viewer | Non-shared User |
|---|---|---|---|---|
| Read Todo | ✅ | ✅ | ✅ | ❌ (404) |
| Update Title/Description | ✅ | ✅ | ❌ (403) | ❌ (404) |
| Toggle Completed | ✅ | ✅ | ❌ (403) | ❌ (404) |
| Delete Todo | ✅ | ❌ (403) | ❌ (403) | ❌ (404) |
| Share / Revoke Share | ✅ | ❌ (403) | ❌ (403) | ❌ (404) |

### Race Conditions & Edge Cases:
1. **Concurrent Update**: Sử dụng Optimistic Locking (`updated_at` check) hoặc PostgreSQL Row-level locking (`SELECT ... FOR UPDATE`).
2. **Owner Revokes Permission Mid-Session**: Mọi API làm mới hoặc sửa Todo luôn truy vấn quyền trực tiếp từ DB/Cache permission trước khi thực hiện thao tác.

---

## 7. Caching & Invalidation Strategy
- Key cache phân quyền: `todo_perm:{todo_id}:{user_id}` -> lưu giá trị `"owner"`, `"editor"`, `"viewer"`. (TTL = 10 phút).
- Khi Owner bấm **Revoke Access** hoặc đổi Role:
  1. Xóa DB record trong `todo_shares`.
  2. Gọi `redis.delete(f"todo_perm:{todo_id}:{collaborator_id}")`.
  3. Xóa cache danh sách todos của collaborator `redis.delete_pattern(f"todos:{collaborator_id}:*")`.
