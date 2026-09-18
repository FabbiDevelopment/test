# Feature Specification: Todo Sharing

## 1. Overview
Tính năng **Todo Sharing** cho phép người dùng (Owner) chia sẻ một công việc (Todo) của họ cho các người dùng khác trong hệ thống. Người được chia sẻ có thể được cấp quyền **Chỉ xem (Read-only)** hoặc **Được phép chỉnh sửa (Edit)**.

---

## 2. Database Schema Changes

Để hỗ trợ việc chia sẻ đa người dùng, chúng ta cần một bảng trung gian (Many-to-Many) để lưu trữ quyền truy cập giữa `User` và `Todo`.

### Bảng mới: `todo_shares`
| Column Name | Data Type | Constraints | Description |
|---|---|---|---|
| `id` | UUID | Primary Key | Định danh duy nhất cho bản ghi chia sẻ |
| `todo_id` | UUID | Foreign Key (`todos.id`), Not Null, ON DELETE CASCADE | Todo đang được chia sẻ |
| `user_id` | UUID | Foreign Key (`users.id`), Not Null, ON DELETE CASCADE | Người dùng được nhận chia sẻ |
| `permission` | VARCHAR(10) | Not Null, Check IN (`'read'`, `'edit'`) | Mức độ quyền hạn |
| `created_at` | TIMESTAMP | Not Null, Default: NOW() | Thời gian chia sẻ |

> **Ràng buộc toàn vẹn (Constraints):** Cần thiết lập `UNIQUE(todo_id, user_id)` để đảm bảo một Todo không bị chia sẻ lặp lại nhiều lần cho cùng một người dùng.

---

## 3. API Endpoints Thiết kế

Các endpoints mới sẽ được đặt trong scope của một `todo_id` cụ thể. 
*(Ghi chú: Tất cả các API này yêu cầu phải đăng nhập - Authenticated)*.

### 3.1. Chia sẻ Todo cho người khác
- **Đường dẫn**: `POST /api/v1/todos/{todo_id}/shares`
- **Request Body**:
  ```json
  {
    "email": "friend@example.com", 
    "permission": "read" 
  }
  ```
- **Response (201 Created)**: Trả về thông tin của `todo_share`.
- **Validation**: Báo lỗi 404 nếu email không tồn tại trong hệ thống.

### 3.2. Cập nhật quyền chia sẻ
- **Đường dẫn**: `PUT /api/v1/todos/{todo_id}/shares/{user_id}`
- **Request Body**: `{"permission": "edit"}`

### 3.3. Thu hồi quyền chia sẻ
- **Đường dẫn**: `DELETE /api/v1/todos/{todo_id}/shares/{user_id}`
- **Response (204 No Content)**.

### 3.4. Lấy danh sách những người đang được chia sẻ (Dành cho Owner)
- **Đường dẫn**: `GET /api/v1/todos/{todo_id}/shares`
- **Response (200 OK)**: Danh sách User ID, Email và Permission.

### 3.5. Xem danh sách Todo được người khác chia sẻ cho mình
- **Đường dẫn**: `GET /api/v1/todos/shared-with-me`
- **Response**: Pagination list các Todos giống như GET `/api/v1/todos`.

---

## 4. Authorization & Security Updates

Đây là phần quan trọng nhất để đảm bảo tính năng chia sẻ không sinh ra lỗi bảo mật (IDOR). Hiện tại, code đang chặn truy cập dựa vào `todo.user_id != current_user.id`. Chúng ta cần viết lại logic này.

### Logic Phân quyền Mới (Access Control Matrix)

1. **Quản lý chia sẻ (Manage Shares - Cấp quyền/Thu hồi)**
   - Chỉ **Owner** (người tạo ra Todo) mới có quyền gọi các API `POST/PUT/DELETE /shares`.

2. **Truy xuất chi tiết Todo (`GET /todos/{id}`)**
   - Được phép nếu `current_user` là **Owner**.
   - HOẶC được phép nếu `current_user` có dòng record trong `todo_shares` ứng với `todo_id` này (Bất kể quyền `read` hay `edit`).
   - Nếu không thỏa mãn -> Ném lỗi `403 Forbidden`.

3. **Cập nhật nội dung Todo (`PUT /todos/{id}`)**
   - Được phép nếu `current_user` là **Owner**.
   - HOẶC được phép nếu `current_user` có record trong `todo_shares` với `permission = 'edit'`.
   - Nếu không thỏa mãn -> Ném lỗi `403 Forbidden`.

4. **Xóa Todo (`DELETE /todos/{id}`)**
   - **Chỉ Owner** mới có quyền xóa vĩnh viễn Todo này khỏi hệ thống. Người được share (dù có quyền edit) cũng không được phép xóa.

### Tối ưu Hiệu năng (Performance)
Thay vì thực hiện 2 câu query rời rạc (1 để tìm Todo, 1 để tìm Share), ta có thể sử dụng SQL `LEFT JOIN` (hoặc `EXISTS`) khi truy vấn lấy Todo để kiểm tra luôn quyền trong 1 vòng kết nối CSDL, giảm tải cho Database. Mọi cập nhật liên quan tới Share cũng cần xóa key Cache của người nhận.
