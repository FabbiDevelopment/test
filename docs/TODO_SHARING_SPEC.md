# Technical Specification: Todo List Sharing Feature

> Technical specification document for Todo List Sharing feature (Task 3A).

---

## 1. Overview & Objective

- **Feature Summary**: Tính năng "Todo Sharing" cho phép người dùng (Owner) chia sẻ toàn bộ danh sách công việc của mình cho người dùng khác trong hệ thống với các mức quyền chi tiết: **Viewer** (chỉ xem) hoặc **Editor** (có quyền thêm, sửa, xóa Todo). Owner có thể thay đổi phân quyền hoặc thu hồi quyền truy cập bất kỳ lúc nào.
- **Problem Statement**: Hiện tại, mỗi người dùng chỉ làm việc độc lập trên danh sách Todo của riêng mình. Người dùng không thể hợp tác, giao việc hoặc chia sẻ danh sách công việc cho đồng nghiệp/người thân.
- **Target Audience / Roles**:
  - **Owner (Chủ sở hữu)**: Người tạo ra Todo, có toàn quyền quản lý, chia sẻ và thu hồi quyền.
  - **Editor (Người chỉnh sửa)**: Người được chia sẻ với quyền `editor`. Được phép xem, tạo mới, chỉnh sửa và đánh dấu hoàn thành/xóa các Todo thuộc danh sách được chia sẻ.
  - **Viewer (Người xem)**: Người được chia sẻ với quyền `viewer`. Chỉ có quyền xem danh sách Todo, không được phép chỉnh sửa hay xóa.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ danh sách Todo cho người dùng khác
- **As an** Owner
- **I want to** nhập email của một người dùng khác và chọn mức quyền (`viewer` hoặc `editor`)
- **So that** tôi có thể hợp tác hoặc chia sẻ công việc cho họ.
- **Acceptance Criteria**:
  - [ ] Hệ thống kiểm tra xem email nhận chia sẻ có tồn tại trong hệ thống hay không.
  - [ ] Không cho phép Owner tự chia sẻ danh sách cho chính mình (Self-sharing prevention). Trả về HTTP 400 Bad Request.
  - [ ] Nếu đã chia sẻ cho email này trước đó, hệ thống ngăn chặn tạo bản ghi trùng lặp và yêu cầu dùng API cập nhật quyền. Trả về HTTP 409 Conflict.
  - [ ] Sau khi chia sẻ thành công, người được chia sẻ sẽ thấy danh sách Todo trong mục "Shared with me".

### User Story 2: Thao tác của Collaborator theo phân quyền
- **As a** Collaborator (Viewer hoặc Editor)
- **I want to** xem hoặc chỉnh sửa danh sách Todo được chia sẻ tương ứng với quyền hạn của mình
- **So that** tôi có thể theo dõi tiến độ hoặc hỗ trợ hoàn thành công việc.
- **Acceptance Criteria**:
  - [ ] **Viewer**: Có thể gửi request `GET /todos` để đọc danh sách. Nếu gửi request `POST`, `PUT`, `DELETE` tới Todo của Owner, hệ thống trả về HTTP 403 Forbidden.
  - [ ] **Editor**: Có thể tạo Todo mới cho Owner, sửa thông tin, đổi trạng thái completed hoặc xóa Todo thuộc sở hữu của Owner.
  - [ ] Cả Viewer và Editor đều KHÔNG có quyền chia sẻ tiếp danh sách này cho người thứ 3 (No re-sharing capability).

### User Story 3: Thu hồi quyền truy cập (Revoke Access)
- **As an** Owner
- **I want to** xóa hoặc thu hồi quyền truy cập của một Collaborator bất kỳ lúc nào
- **So that** tôi kiểm soát an toàn dữ liệu công việc của mình.
- **Acceptance Criteria**:
  - [ ] Owner bấm thu hồi quyền, bản ghi chia sẻ bị xóa khỏi hệ thống.
  - [ ] Ngay lập tức, tất cả Redis Cache liên quan đến danh sách được chia sẻ của Collaborator đó bị xóa (Cache Invalidation).
  - [ ] Mọi request tiếp theo từ Collaborator tới dữ liệu của Owner sẽ nhận lại kết quả HTTP 403 Forbidden hoặc 404 Not Found.

---

## 3. Scope

### In-Scope (Thuộc phạm vi phiên bản V1)
- Chia sẻ danh sách Todo trực tiếp giữa User với User qua Email.
- Phân quyền theo 2 mức độ rõ ràng: `viewer` và `editor`.
- Quản lý danh sách người được chia sẻ, thay đổi cấp độ quyền và thu hồi quyền.
- Hệ thống vô hiệu hóa Cache ngay lập tức khi thu hồi quyền hoặc thay đổi dữ liệu.

### Out-of-Scope (Loại trừ khỏi V1 để giữ release gọn nhẹ)
- Chia sẻ từng item Todo riêng lẻ (V1 chỉ hỗ trợ chia sẻ theo cấp độ toàn bộ danh sách).
- Chia sẻ qua đường link công khai (Public link) không cần đăng nhập.
- Giới hạn thời gian chia sẻ (Expiration timer).
- Nhật ký hoạt động chi tiết (Audit log / Activity feed).

---

## 4. Database Design (SQL Implementation)

```sql
-- Kích hoạt extension hỗ trợ tạo UUID ngẫu nhiên (nếu chưa có)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Bảng lưu trữ thông tin chia sẻ danh sách Todo giữa các người dùng
CREATE TABLE todo_shares (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),                       -- Định danh duy nhất của bản ghi chia sẻ (Primary Key)
    owner_id UUID NOT NULL,                                              -- ID người chủ sở hữu Todo List (Foreign Key -> users.id)
    shared_with_user_id UUID NOT NULL,                                    -- ID người được nhận chia sẻ (Foreign Key -> users.id)
    permission_level VARCHAR(20) NOT NULL,                                -- Cấp độ quyền truy cập ('viewer' hoặc 'editor')
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,            -- Thời gian tạo bản ghi chia sẻ
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,            -- Thời gian cập nhật bản ghi gần nhất

    -- Ràng buộc khóa ngoại (Foreign Keys) với cơ chế CASCADE DELETE
    CONSTRAINT fk_todo_shares_owner 
        FOREIGN KEY (owner_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,                                                -- Tự động xóa các bản ghi chia sẻ nếu tài khoản Owner bị xóa

    CONSTRAINT fk_todo_shares_shared_with 
        FOREIGN KEY (shared_with_user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,                                                -- Tự động xóa các bản ghi chia sẻ nếu tài khoản Collaborator bị xóa

    -- Ràng buộc duy nhất (Unique Constraint)
    CONSTRAINT uq_todo_shares_owner_shared_with 
        UNIQUE (owner_id, shared_with_user_id),                          -- Đảm bảo không tạo 2 bản ghi chia sẻ trùng lặp giữa 2 người dùng

    -- Ràng buộc kiểm tra giá trị (Check Constraints)
    CONSTRAINT chk_todo_shares_permission_level 
        CHECK (permission_level IN ('viewer', 'editor')),                 -- Chỉ cho phép giá trị quyền là 'viewer' hoặc 'editor'

    CONSTRAINT chk_prevent_self_share 
        CHECK (owner_id != shared_with_user_id)                          -- Ngăn chặn người dùng tự chia sẻ danh sách Todo cho chính mình
);

-- Tối ưu hóa chỉ mục (Indexes)
CREATE INDEX ix_todo_shares_shared_with_user 
    ON todo_shares (shared_with_user_id, permission_level);              -- Tối ưu truy vấn tìm nhanh danh sách Todo mà user này được chia sẻ

CREATE INDEX ix_todo_shares_owner_id 
    ON todo_shares (owner_id);                                            -- Tối ưu truy vấn lấy danh sách những người được Owner chia sẻ
```

---

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/todos/shares` | Chia sẻ danh sách Todo cho user khác qua email | Yes (Owner) |
| `GET` | `/api/v1/todos/shares` | Lấy danh sách các lượt chia sẻ (cả đi và đến) | Yes |
| `PATCH` | `/api/v1/todos/shares/{share_id}` | Cập nhật mức quyền (`viewer` <-> `editor`) | Yes (Owner) |
| `DELETE` | `/api/v1/todos/shares/{share_id}` | Thu hồi quyền truy cập | Yes (Owner) |
| `GET` | `/api/v1/todos/shared-with-me` | Lấy danh sách Todos được người khác chia sẻ | Yes |

### Request & Response Schemas

#### 1. `POST /api/v1/todos/shares`
**Request Body**:
```json
{
  "email": "collaborator@example.com",
  "permission_level": "editor"
}
```

**Response Success (201 Created)**:
```json
{
  "id": "c39a2b8e-9d10-4f51-8721-6a2d9c123456",
  "owner_id": "11111111-1111-1111-1111-111111111111",
  "shared_with_user_id": "22222222-2222-2222-2222-222222222222",
  "shared_with_email": "collaborator@example.com",
  "permission_level": "editor",
  "created_at": "2026-09-19T22:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: `{"detail": "Cannot share todo list with yourself"}`
- `404 Not Found`: `{"detail": "User with specified email not found"}`
- `409 Conflict`: `{"detail": "Todo list is already shared with this user"}`

---

## 6. Business Logic & Security Considerations

### Permission Matrix

| Operation | Owner | Editor | Viewer | Non-collaborator |
|---|:---:|:---:|:---:|:---:|
| Read Todos | ✅ | ✅ | ✅ | ❌ (404/403) |
| Create Todo | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Update Todo | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Delete Todo | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Share List | ✅ | ❌ (403) | ❌ (403) | ❌ (403) |
| Revoke Access | ✅ | ❌ (403) | ❌ (403) | ❌ (403) |

### Race Conditions & Edge Cases
1. **Revoke during active editing**: Nếu Owner thu hồi quyền đúng lúc Editor đang gửi request `PUT /todos/{id}`, middleware/dependency check sẽ thực hiện kiểm tra quyền truy cập trực tiếp trong database (hoặc Redis cache) ngay tại thời điểm xử lý request. Request sửa của Editor sẽ nhận lại `403 Forbidden`.
2. **Concurrent Permission Downgrade**: Nếu Owner hạ quyền từ `editor` xuống `viewer`, request ghi tiếp theo của Collaborator sẽ ngay lập tức bị từ chối với mã lỗi `403 Forbidden`.

---

## 7. Caching & Invalidation Strategy

- **Redis Cache Key Naming**:
  - `todos:owner:{owner_id}:list:*` - Cache danh sách Todo của Owner.
  - `todos:shared_with:{user_id}:list:*` - Cache danh sách Todo mà `user_id` được xem.
  - `todos:permissions:{owner_id}:{user_id}` - Cache mức quyền truy cập giữa Owner và User (`viewer` / `editor`).

- **Cache Invalidation Rules**:
  - Khi Owner **chia sẻ mới** hoặc **thay đổi quyền**: Xóa cache `todos:permissions:{owner_id}:{user_id}` và `todos:shared_with:{user_id}:list:*`.
  - Khi Owner **thu hồi quyền**: Ngay lập tức xóa `todos:permissions:{owner_id}:{user_id}` và toàn bộ cache `todos:shared_with:{user_id}:*`.
  - Khi Editor **tạo/sửa/xóa Todo**: Xóa đồng thời cache danh sách của Owner `todos:owner:{owner_id}:list:*` và cache của tất cả các Collaborator liên quan.
