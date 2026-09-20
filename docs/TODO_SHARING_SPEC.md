# Technical Specification: Todo List Collaboration & Sharing

> **Status**: Proposed  
> **Author**: Nguyen Quang Huy  
> **Target Release**: Q4/2026  
> **Document Version**: 1.0.0  

---

## 1. Overview & Objective

### 1.1 Feature Summary
Tính năng **Todo List Collaboration & Sharing** cho phép người dùng chia sẻ danh sách Todo của mình với những người dùng khác trong hệ thống theo cơ chế phân quyền theo vai trò (Role-Based Access Control - RBAC). Người được chia sẻ có thể có quyền chỉ đọc (`viewer`) hoặc quyền chỉnh sửa (`editor`). Chủ sở hữu (`owner`) có toàn quyền cấp quyền, thay đổi quyền hoặc thu hồi quyền truy cập bất kỳ lúc nào.

### 1.2 Problem Statement
Hiện tại, ứng dụng Todo hoạt động theo mô hình cô lập dữ liệu tuyệt đối (single-user isolated model). Mỗi người dùng chỉ có thể quản lý danh sách Todo cá nhân. Trong thực tế công việc và đời sống (quản lý công việc gia đình, làm việc nhóm, chia sẻ checklist dự án), người dùng có nhu cầu cộng tác trên cùng một danh sách công việc mà không muốn chia sẻ tài khoản hay mật khẩu.

### 1.3 Target Audience & Roles
- **Owner (Chủ sở hữu)**: Người tạo ra danh sách Todo. Có toàn quyền cao nhất: thêm/sửa/xóa Todo, chia sẻ danh sách, phân quyền `viewer`/`editor`, thay đổi quyền và thu hồi quyền chia sẻ bất kỳ lúc nào.
- **Editor (Cộng tác viên chỉnh sửa)**: Người được chia sẻ với quyền `editor`. Có thể xem danh sách, tạo Todo mới trong danh sách được chia sẻ, chỉnh sửa nội dung Todo và đánh dấu hoàn thành/chưa hoàn thành. Không có quyền xóa danh sách của Owner, không có quyền mời thêm người khác hoặc thu hồi quyền của người khác.
- **Viewer (Người xem)**: Người được chia sẻ với quyền `viewer`. Chỉ có quyền xem danh sách Todo (Read-only). Không thể tạo, sửa, đổi trạng thái hay xóa Todo.

---

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ danh sách Todo với người dùng khác
- **As an** Owner
- **I want to** nhập email của người dùng khác và chọn vai trò (`viewer` hoặc `editor`) để chia sẻ danh sách Todo của tôi
- **So that** họ có thể xem hoặc cùng tôi xử lý các đầu việc.
- **Acceptance Criteria**:
  - [ ] Người dùng nhập email người nhận và chọn quyền (`viewer` hoặc `editor`).
  - [ ] Hệ thống kiểm tra: Email phải tồn tại trong hệ thống; không được tự chia sẻ cho chính mình (Self-sharing); không được chia sẻ trùng lặp nếu đã chia sẻ trước đó.
  - [ ] Nếu thông tin hợp lệ, hệ thống tạo bản ghi chia sẻ mới và gửi thông báo thành công.
  - [ ] Người nhận ngay lập tức thấy danh sách này trong mục "Shared with me".

### User Story 2: Quyền thao tác của Editor
- **As an** Editor
- **I want to** thêm mới công việc, cập nhật tiêu đề/mô tả và đánh dấu hoàn thành các Todo trong danh sách được chia sẻ
- **So that** tôi có thể chủ động cập nhật tiến độ công việc chung.
- **Acceptance Criteria**:
  - [ ] Editor có thể gọi API tạo Todo mới gắn với `owner_id` của danh sách được chia sẻ.
  - [ ] Editor có thể cập nhật `title`, `description`, `completed` của các Todo thuộc danh sách này.
  - [ ] Editor không thể xóa vĩnh viễn toàn bộ danh sách Todo của Owner.
  - [ ] Mọi thay đổi của Editor được đồng bộ tức thì cho Owner và các thành viên khác.

### User Story 3: Trải nghiệm chỉ đọc của Viewer
- **As a** Viewer
- **I want to** xem danh sách các Todo được chia sẻ và theo dõi tiến độ
- **So that** tôi nắm được thông tin mà không vô tình chỉnh sửa làm sai lệch dữ liệu.
- **Acceptance Criteria**:
  - [ ] Viewer có thể xem danh sách công việc, chi tiết từng Todo.
  - [ ] Giao diện ẩn/disable các nút tạo Todo, sửa Todo, checkbox hoàn thành và nút xóa.
  - [ ] Nếu Viewer cố tình gọi API tạo/sửa/xóa qua cURL/Postman, Backend từ chối với mã lỗi `403 Forbidden`.

### User Story 4: Thu hồi hoặc điều chỉnh quyền truy cập
- **As an** Owner
- **I want to** đổi quyền từ `viewer` sang `editor` (hoặc ngược lại), hoặc xóa người dùng khỏi danh sách chia sẻ
- **So that** tôi kiểm soát hoàn toàn việc ai được phép tiếp cận dữ liệu của tôi.
- **Acceptance Criteria**:
  - [ ] Owner có thể xem danh sách tất cả những người đang được chia sẻ kèm vai trò hiện tại.
  - [ ] Owner có thể cập nhật quyền (`PATCH /shares/{share_id}`).
  - [ ] Owner có thể thu hồi quyền (`DELETE /shares/{share_id}`).
  - [ ] Ngay khi bị thu hồi, quyền truy cập của người đó chấm dứt ngay lập tức (Cache bị xóa, request tiếp theo bị từ chối `403 Forbidden`).

---

## 3. Scope

### 3.1 In-Scope (Phiên bản V1)
- Chia sẻ danh sách Todo trực tiếp thông qua email của người dùng đã đăng ký tài khoản.
- Hai cấp độ phân quyền rõ ràng: `viewer` (chỉ đọc) và `editor` (đọc & ghi).
- Quản lý danh sách chia sẻ: Xem danh sách thành viên, cập nhật quyền, thu hồi quyền (bởi Owner).
- Xem danh sách công việc được chia sẻ: Tab "My Todos" và tab "Shared with Me".
- Cơ chế Invalidate Cache Redis tức thì khi có cập nhật hoặc thu hồi quyền.

### 3.2 Out-of-Scope (Dành cho các phiên bản tiếp theo)
- Chia sẻ công khai qua liên kết công cộng (Public URL link sharing không cần đăng nhập).
- Gửi email thông báo qua SMTP / Mail Server khi có lời mời chia sẻ.
- Chia sẻ chi tiết ở cấp độ từng Todo riêng lẻ (V1 áp dụng chia sẻ toàn bộ danh sách Todo của User).
- Lịch sử chỉnh sửa chi tiết (Audit Trail / Revision History - ai sửa lúc nào).
- Cộng tác thời gian thực qua WebSockets (Real-time collaborative editing). V1 sử dụng cơ chế invalidation của React Query và cache TTL ngắn.

---

## 4. Database Design

### 4.1 Schema Definition: Bảng `todo_shares`

```sql
CREATE TABLE todo_shares (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    owner_id UUID NOT NULL,
    shared_with_user_id UUID NOT NULL,
    permission VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    -- Ràng buộc khóa ngoại
    CONSTRAINT fk_todo_shares_owner 
        FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_todo_shares_shared_with 
        FOREIGN KEY (shared_with_user_id) REFERENCES users(id) ON DELETE CASCADE,

    -- Ràng buộc tính hợp lệ của quyền hạn
    CONSTRAINT chk_valid_permission 
        CHECK (permission IN ('viewer', 'editor')),

    -- Ràng buộc không cho phép tự chia sẻ cho chính mình
    CONSTRAINT chk_no_self_share 
        CHECK (owner_id != shared_with_user_id),

    -- Ràng buộc không cho phép chia sẻ trùng lặp
    CONSTRAINT uq_owner_shared_with 
        UNIQUE (owner_id, shared_with_user_id)
);
```

### 4.2 Indexes & Performance Tuning
1. **Index tìm kiếm danh sách chia sẻ của người nhận**:
   ```sql
   CREATE INDEX idx_todo_shares_shared_with 
       ON todo_shares (shared_with_user_id, permission);
   ```
   *Mục đích*: Tối ưu truy vấn khi User mở tab "Shared with Me" và khi middleware kiểm tra quyền truy cập của collaborator.

2. **Index tìm kiếm danh sách thành viên của Owner**:
   ```sql
   CREATE INDEX idx_todo_shares_owner 
       ON todo_shares (owner_id);
   ```
   *Mục đích*: Tối ưu khi Owner mở modal quản lý cộng tác viên hoặc khi cascade xóa tài khoản.

---

## 5. API Contracts & Endpoints

### 5.1 Danh sách Endpoints

| Method | Endpoint | Mô tả | Vai trò yêu cầu |
|---|---|---|---|
| `POST` | `/api/v1/shares` | Chia sẻ danh sách Todo cho một user | Owner |
| `GET` | `/api/v1/shares` | Lấy danh sách những người đang được mình chia sẻ | Owner |
| `PATCH` | `/api/v1/shares/{share_id}` | Cập nhật vai trò (`viewer` $\leftrightarrow$ `editor`) | Owner |
| `DELETE` | `/api/v1/shares/{share_id}` | Thu hồi quyền chia sẻ | Owner hoặc Collaborator tự rời |
| `GET` | `/api/v1/shares/shared-with-me` | Lấy danh sách các Todo list được người khác chia sẻ | Authenticated User |
| `GET` | `/api/v1/todos?owner_id={uuid}` | Lấy danh sách Todo (của mình hoặc được chia sẻ) | Owner / Editor / Viewer |
| `POST` | `/api/v1/todos?owner_id={uuid}` | Tạo Todo trong danh sách (của mình hoặc được chia sẻ) | Owner / Editor |

---

### 5.2 Request & Response Schemas

#### 1. `POST /api/v1/shares`
**Request Body**:
```json
{
  "email": "collaborator@example.com",
  "permission": "editor"
}
```
**Validation Rules**:
- `email`: Email hợp lệ, không được trùng với email của `current_user`.
- `permission`: Chỉ chấp nhận `"viewer"` hoặc `"editor"`.

**Response (201 Created)**:
```json
{
  "id": "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
  "owner_id": "11111111-2222-3333-4444-555555555555",
  "shared_with_user_id": "66666666-7777-8888-9999-000000000000",
  "shared_with_email": "collaborator@example.com",
  "permission": "editor",
  "created_at": "2026-09-20T00:00:00Z",
  "updated_at": "2026-09-20T00:00:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: `{ "detail": "Cannot share todo list with yourself" }`
- `404 Not Found`: `{ "detail": "User with this email not found" }`
- `409 Conflict`: `{ "detail": "This user already has access to your todo list" }`

---

#### 2. `PATCH /api/v1/shares/{share_id}`
**Request Body**:
```json
{
  "permission": "viewer"
}
```
**Response (200 OK)**: Trả về đối tượng share đã cập nhật permission.

---

#### 3. `DELETE /api/v1/shares/{share_id}`
**Response (204 No Content)**: Thu hồi quyền thành công, không trả về body.

---

## 6. Business Logic & Security Considerations

### 6.1 Permission Matrix (Ma trận phân quyền)

| Thao tác | Owner | Editor | Viewer | Người lạ |
|---|:---:|:---:|:---:|:---:|
| Xem danh sách Todo | ✅ | ✅ | ✅ | ❌ (404/403) |
| Xem chi tiết Todo | ✅ | ✅ | ✅ | ❌ (404/403) |
| Tạo mới Todo | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Cập nhật Todo (Title/Desc/Status) | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Xóa một Todo | ✅ | ✅ | ❌ (403) | ❌ (404/403) |
| Mời người khác vào danh sách | ✅ | ❌ (403) | ❌ (403) | ❌ (403) |
| Thay đổi quyền của thành viên | ✅ | ❌ (403) | ❌ (403) | ❌ (403) |
| Thu hồi quyền của thành viên | ✅ | ❌ (403) | ❌ (403) | ❌ (403) |
| Tự rời khỏi danh sách chia sẻ | N/A | ✅ | ✅ | ❌ |

---

### 6.2 Edge Cases & Race Conditions

1. **Tự chia sẻ cho chính mình (Self-sharing)**:
   - *Nguy cơ*: Gây lỗi logic vòng lặp dữ liệu và phân trang.
   - *Giải pháp*: Bắt lỗi ở 2 lớp:
     - Lớp Service/Pydantic: `if target_user.id == current_user.id: raise HTTPException(400)`.
     - Lớp Database: Ràng buộc `CONSTRAINT chk_no_self_share CHECK (owner_id != shared_with_user_id)`.

2. **Chia sẻ trùng lặp (Duplicate Invites)**:
   - *Nguy cơ*: Tạo nhiều bản ghi share với cùng một user, gây mâu thuẫn quyền hạn.
   - *Giải pháp*: Ràng buộc `UNIQUE (owner_id, shared_with_user_id)` đảm bảo tính toàn vẹn ở tầng dữ liệu. Backend trả về `409 Conflict` nếu bản ghi đã tồn tại.

3. **Thu hồi quyền đồng thời (Race Condition: Revoke vs Edit)**:
   - *Nguy cơ*: Owner vừa bấm thu hồi quyền của Editor thì đúng lúc đó Editor gửi request `PUT /todos/{id}`.
   - *Giải pháp*: Mọi thao tác ghi của Editor đều kiểm tra quyền trong cùng một database transaction:
     ```sql
     SELECT permission FROM todo_shares 
     WHERE owner_id = :owner_id AND shared_with_user_id = :current_user_id;
     ```
     Nếu không còn bản ghi hoặc `permission != 'editor'`, lập tức abort transaction và trả về `403 Forbidden`.

4. **Xóa tài khoản Owner (Cascade Cleanup)**:
   - *Giải pháp*: Cấu hình `ON DELETE CASCADE` trên cả 2 khóa ngoại `owner_id` và `shared_with_user_id`. Nếu tài khoản Owner hoặc Collaborator bị xóa, toàn bộ bản ghi chia sẻ liên quan tự động được giải phóng sạch sẽ.

---

## 7. Caching & Invalidation Strategy

### 7.1 Cấu trúc Redis Cache Key
Để hỗ trợ tính năng chia sẻ mà không gây rò rỉ dữ liệu giữa các người dùng:
- Cache danh sách Todo của chính chủ:
  `todos:user:{owner_id}:page:{page}:size:{size}`
- Cache danh sách Todo được chia sẻ (tùy biến theo góc nhìn người nhận):
  `todos:shared:owner:{owner_id}:viewer:{collaborator_id}:page:{page}:size:{size}`

### 7.2 Chiến lược Invalidation (Xóa cache tức thì)

| Sự kiện | Hành động Invalidate Cache |
|---|---|
| **Owner hoặc Editor tạo/sửa/xóa Todo** | Xóa toàn bộ cache của Owner: `todos:user:{owner_id}:*`<br>Đồng thời xóa toàn bộ cache chia sẻ: `todos:shared:owner:{owner_id}:*` |
| **Owner thay đổi quyền (`PATCH /shares`)** | Xóa cache chia sẻ của collaborator đó: `todos:shared:owner:{owner_id}:viewer:{collaborator_id}:*` |
| **Owner thu hồi quyền (`DELETE /shares`)** | Xóa ngay cache chia sẻ: `todos:shared:owner:{owner_id}:viewer:{collaborator_id}:*` để collaborator không thể đọc dữ liệu cũ từ RAM |
| **Collaborator tự rời khỏi danh sách** | Xóa ngay cache chia sẻ: `todos:shared:owner:{owner_id}:viewer:{collaborator_id}:*` |

*Thời gian sống dự phòng (TTL)*: 300 giây (5 phút) cho tất cả các cache key để phòng ngừa trường hợp cache miss hoặc lỗi kết nối Redis.
