# Technical Specification: Collaborative Todo Sharing & Permissions

## 1. Overview & Objective
- **Feature Summary**: Tính năng chia sẻ danh sách công việc (Todo List Sharing) cho phép chủ sở hữu danh sách (Owner) cấp quyền truy cập danh sách công việc của mình cho người dùng khác với các mức phân quyền linh hoạt: **Xem (Viewer - Read-only)** hoặc **Chỉnh sửa (Editor - Full Edit)**, đồng thời cho phép chủ sở hữu thu hồi quyền (Revoke) bất kỳ lúc nào.
- **Problem Statement**: Hiện tại, ứng dụng phân lập dữ liệu độc lập 100% giữa các người dùng. Người dùng không thể cộng tác làm việc nhóm, chia sẻ tiến độ công việc hoặc phân công nhiệm vụ cho đồng nghiệp/thành viên gia đình trong cùng hệ thống.
- **Target Audience / Roles**:
  - **Owner (Chủ sở hữu)**: Người tạo ra danh sách Todo. Có toàn quyền quản lý Todo, chia sẻ cho người khác, thay đổi quyền hoặc thu hồi quyền truy cập.
  - **Editor (Người cộng tác - Chỉnh sửa)**: Người được chia sẻ với vai trò Editor. Có quyền đọc, tạo mới, chỉnh sửa nội dung, toggle trạng thái hoàn thành các todo trong danh sách được chia sẻ; không có quyền xóa danh sách, không có quyền xóa todo vĩnh viễn hoặc mời thêm người khác.
  - **Viewer (Người xem - Chỉ đọc)**: Người được chia sẻ với vai trò Viewer. Chỉ có quyền xem danh sách và chi tiết các công việc; không thể thay đổi dữ liệu.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ danh sách công việc với quyền Viewer / Editor
- **As an** Owner của một danh sách công việc,
- **I want to** nhập email của người dùng khác và chọn vai trò `VIEWER` hoặc `EDITOR`,
- **So that** họ có thể xem hoặc cùng cập nhật các công việc theo đúng quyền hạn.
- **Acceptance Criteria**:
  - [ ] Owner có thể tìm và gửi lời mời chia sẻ qua email của người nhận đã đăng ký trong hệ thống.
  - [ ] Hệ thống chặn và báo lỗi nếu Owner tự chia sẻ cho chính mình (Self-sharing prevention).
  - [ ] Hệ thống chặn việc chia sẻ trùng lặp (nếu đã chia sẻ trước đó, yêu cầu dùng API cập nhật quyền).
  - [ ] Người nhận (Collaborator) sau khi được share sẽ thấy danh sách công việc trong mục "Shared with me".

### User Story 2: Phân quyền thao tác trên Todo được chia sẻ
- **As a** Collaborator (Viewer/Editor),
- **I want** hệ thống áp dụng chính xác giới hạn phân quyền theo vai trò của tôi,
- **So that** tôi không thể vô tình hay cố ý thực hiện các hành động vượt quá thẩm quyền.
- **Acceptance Criteria**:
  - [ ] **Viewer**: Có thể xem danh sách và chi tiết todo; bất kỳ thao tác tạo mới, sửa, xóa, toggle complete đều bị chặn với HTTP `403 Forbidden`.
  - [ ] **Editor**: Có thể tạo mới todo vào danh sách chia sẻ, sửa title/description, toggle checkbox completed; không thể xóa todo của Owner hoặc chia sẻ tiếp cho bên thứ ba.
  - [ ] Phản hồi API ghi nhận rõ ràng `created_by` và `updated_by` để phục vụ audit trail.

### User Story 3: Thu hồi và thay đổi quyền truy cập tức thì (Revocation & Role Update)
- **As an** Owner,
- **I want to** thay đổi vai trò (Viewer <-> Editor) hoặc thu hồi quyền truy cập của một cộng tác viên bất cứ lúc nào,
- **So that** tôi kiểm soát hoàn toàn tính bảo mật của dữ liệu cá nhân.
- **Acceptance Criteria**:
  - [ ] Owner có thể xóa quyền truy cập (Revoke) của bất kỳ collaborator nào.
  - [ ] Ngay khi quyền bị thu hồi, Redis cache của collaborator bị xóa ngay lập tức. Mọi request tiếp theo từ collaborator đó lập tức nhận HTTP `403 Forbidden` / `404 Not Found`.

---

## 3. Scope

### In-Scope (Phiên bản V1):
- Quản lý phân quyền danh sách Todo ở cấp độ User-to-User: Bảng `todo_shares`.
- 2 cấp độ phân quyền rõ ràng: `VIEWER` (Read) và `EDITOR` (Read + Write).
- API chia sẻ, cập nhật vai trò, xem danh sách người được chia sẻ, và thu hồi quyền (Revoke).
- Tích hợp bảo vệ phân quyền tầng API Service & Dependency Injection trong FastAPI.
- Cơ chế Invalidate Redis Cache tức thì khi thay đổi quyền hạn.

### Out-of-Scope (Dành cho phiên bản sau - Tránh Scope Creep):
- Chia sẻ công khai qua liên kết nặc danh (Public link sharing).
- Lời mời qua email cho người chưa đăng ký tài khoản (Email invite tokens/magic links).
- Hệ thống thông báo thời gian thực (WebSockets / Push Notifications).
- Phân quyền theo nhóm người dùng (Team/Workspace/Organization groups).
- Khôi phục Todo đã xóa (Soft delete / Trash bin).

---

## 4. Database Design

### New Table: `todo_shares`

```sql
CREATE TYPE share_role AS ENUM ('VIEWER', 'EDITOR');

CREATE TABLE todo_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    shared_with_user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role share_role NOT NULL DEFAULT 'VIEWER',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT uq_owner_shared_user UNIQUE (owner_id, shared_with_user_id),
    CONSTRAINT chk_no_self_sharing CHECK (owner_id != shared_with_user_id)
);
```

### Constraints & Indexes:
1. **Primary Key**: `id (UUID)`.
2. **Foreign Keys**:
   - `owner_id` -> `users(id)` với `ON DELETE CASCADE`.
   - `shared_with_user_id` -> `users(id)` với `ON DELETE CASCADE`.
3. **Unique Constraint**: `(owner_id, shared_with_user_id)` đảm bảo một user chỉ có tối đa 1 bản ghi quyền trên danh sách của owner.
4. **Check Constraint**: `owner_id != shared_with_user_id` ngăn chặn tự chia sẻ cho bản thân ở cấp cơ sở dữ liệu.
5. **Indexes**:
   - `CREATE INDEX idx_todo_shares_shared_with ON todo_shares(shared_with_user_id);` (Tối ưu truy vấn tìm danh sách mà user được chia sẻ).
   - `CREATE INDEX idx_todo_shares_owner_role ON todo_shares(owner_id, role);` (Tối ưu kiểm tra quyền hạn khi truy xuất dữ liệu).

---

## 5. API Contracts & Endpoints

### 5.1 Bảng tổng hợp Endpoints

| HTTP Method | Endpoint | Description | Roles Allowed |
|---|---|---|---|
| `POST` | `/api/v1/shares` | Chia sẻ danh sách cho một người dùng khác | Owner |
| `GET` | `/api/v1/shares` | Danh sách những người đang được chia sẻ danh sách của tôi | Owner |
| `GET` | `/api/v1/shares/shared-with-me` | Danh sách các owner đã chia sẻ danh sách cho tôi | Authenticated User |
| `PATCH` | `/api/v1/shares/{share_id}` | Thay đổi quyền hạn (VIEWER <-> EDITOR) | Owner |
| `DELETE` | `/api/v1/shares/{share_id}` | Thu hồi quyền chia sẻ (Revoke) | Owner / Collaborator (Leave) |
| `GET` | `/api/v1/shares/{owner_id}/todos` | Xem danh sách Todo của Owner được chia sẻ | Viewer, Editor, Owner |

### 5.2 Schemas & Payloads

#### Request: `POST /api/v1/shares`
```json
{
  "email": "colleague@example.com",
  "role": "EDITOR"
}
```
*Validation*: Email phải hợp lệ và tồn tại trong hệ thống; `role` thuộc enum `['VIEWER', 'EDITOR']`.

#### Response: `201 Created`
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "owner_id": "00000000-0000-0000-0000-000000000001",
  "shared_with_user_id": "00000000-0000-0000-0000-000000000002",
  "shared_with_email": "colleague@example.com",
  "role": "EDITOR",
  "created_at": "2026-09-19T10:00:00Z",
  "updated_at": "2026-09-19T10:00:00Z"
}
```

#### Error Responses:
- `400 Bad Request`: `{ "detail": "Cannot share todos with yourself" }`
- `404 Not Found`: `{ "detail": "User with specified email not found" }`
- `409 Conflict`: `{ "detail": "Share invitation already exists for this user" }`
- `403 Forbidden`: `{ "detail": "You do not have permission to perform this action" }`

---

## 6. Business Logic & Security Considerations

### 6.1 Ma trận phân quyền (Authorization Matrix)

| Thao tác / Tài nguyên | Owner | Editor | Viewer | Người lạ (Unshared) |
|---|:---:|:---:|:---:|:---:|
| `GET` Xem danh sách / Chi tiết Todo |  Cho phép |  Cho phép |  Cho phép |  Chặn (404/403) |
| `POST` Thêm Todo mới vào danh sách |  Cho phép |  Cho phép |  Chặn (403) |  Chặn (403) |
| `PUT` Sửa Todo / Đổi trạng thái completed |  Cho phép |  Cho phép |  Chặn (403) |  Chặn (403) |
| `DELETE` Xóa Todo |  Cho phép |  Chặn (403)* |  Chặn (403) |  Chặn (403) |
| `POST` Mời / Thu hồi người khác |  Cho phép |  Chặn (403) |  Chặn (403) |  Chặn (403) |

*\* Lưu ý: Editor không có quyền xóa vĩnh viễn Todo của Owner để ngăn ngừa mất dữ liệu ngoài ý muốn.*

### 6.2 Xử lý Edge Cases & Race Conditions
1. **Tự chia sẻ cho chính mình (Self-sharing)**:
   - Kiểm tra ngay tại tầng Service: `if current_user.email == request.email: raise HTTPException(400, "Cannot share with self")`.
   - Ràng buộc Check constraint ở Database layer chặn triệt để.
2. **Chia sẻ trùng lặp (Duplicate Share)**:
   - Database Unique constraint `uq_owner_shared_user` sinh lỗi IntegrityError -> Chuyển thành HTTP `409 Conflict`.
3. **Race Condition khi thu hồi quyền (Concurrent Revoke vs Edit)**:
   - Nếu Owner thu hồi quyền trong khi Editor đang gửi request cập nhật Todo: Request của Editor sẽ kiểm tra quyền trong transaction database (hoặc kiểm tra Redis session permission). Nếu quyền đã bị xóa, request trả về `403 Forbidden` và rollback transaction.

---

## 7. Caching & Invalidation Strategy

### 7.1 Cấu trúc Redis Cache Keys
- Cache danh sách Todo của Owner: `todos:user:{owner_id}:*`
- Cache quyền hạn của Collaborator: `permissions:user:{user_id}:owner:{owner_id}` -> lưu `"EDITOR"` hoặc `"VIEWER"` (TTL: 10 phút).
- Cache danh sách người được chia sẻ: `shares:owner:{owner_id}` (TTL: 5 phút).

### 7.2 Quy tắc Invalidation (Xóa cache tức thì):
1. **Khi Owner chia sẻ hoặc cập nhật Role**:
   - Xóa `shares:owner:{owner_id}`.
   - Xóa `permissions:user:{collaborator_id}:owner:{owner_id}`.
2. **Khi Owner thu hồi quyền (Revoke)**:
   - Xóa `permissions:user:{collaborator_id}:owner:{owner_id}`.
   - Xóa cache danh sách Todo phía collaborator: `todos:shared:user:{collaborator_id}:*`.
3. **Khi Editor tạo hoặc cập nhật Todo**:
   - Xóa toàn bộ cache Todo của Owner: `todos:user:{owner_id}:*`.
   - Xóa toàn bộ cache Todo được chia sẻ của tất cả collaborator liên quan.
