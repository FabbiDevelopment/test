# Technical Specification: Todo Sharing

## 1. Overview & Objective
- **Feature Summary**: Cho phép người dùng chia sẻ các công việc (Todo) của mình với người dùng khác kèm theo phân quyền cụ thể: Xem (Viewer) hoặc Sửa (Editor). Chủ sở hữu (Owner) có quyền thu hồi quyền truy cập bất cứ lúc nào.
- **Problem Statement**: Hiện tại, mỗi Todo bị cô lập hoàn toàn cho từng người dùng, gây khó khăn trong việc cộng tác nhóm hoặc giao việc. Tính năng này giải quyết nhu cầu chia sẻ thông tin công việc một cách an toàn và có kiểm soát.
- **Target Audience / Roles**: 
  - **Owner**: Người tạo ra Todo, có toàn quyền chia sẻ, sửa, xóa, và thu hồi quyền.
  - **Viewer (Read-only)**: Người được chia sẻ với quyền chỉ xem nội dung.
  - **Editor (Edit)**: Người được chia sẻ với quyền xem và chỉnh sửa nội dung/trạng thái của Todo.

## 2. User Stories & Acceptance Criteria

### User Story 1: Chia sẻ Todo
- **As an** Owner
- **I want to** chia sẻ một Todo của tôi cho người dùng khác thông qua email của họ với các mức quyền (Viewer hoặc Editor)
- **So that** họ có thể xem hoặc giúp tôi cập nhật tiến độ công việc.
- **Acceptance Criteria**:
  - [ ] Owner có thể nhập email của người dùng hệ thống để chia sẻ Todo.
  - [ ] Owner phải chọn một trong 2 quyền: `viewer` hoặc `editor`.
  - [ ] Hệ thống báo lỗi 404 nếu email người dùng không tồn tại.
  - [ ] Hệ thống báo lỗi 400 nếu Owner tự chia sẻ cho chính mình (Self-sharing).
  - [ ] Hệ thống báo lỗi 409 nếu người này đã được chia sẻ trước đó (Duplicate invites).

### User Story 2: Quyền truy cập của Collaborator
- **As a** Collaborator (Viewer/Editor)
- **I want to** truy cập vào các Todo đã được chia sẻ với tôi
- **So that** tôi có thể xem hoặc sửa nội dung theo quyền được cấp.
- **Acceptance Criteria**:
  - [ ] Viewer có thể gọi API GET để lấy thông tin Todo, nhưng gọi PUT/DELETE sẽ bị lỗi 403 Forbidden.
  - [ ] Editor có thể gọi API GET và PUT để sửa tiêu đề, nội dung, hoặc trạng thái.
  - [ ] Cả Viewer và Editor đều KHÔNG THỂ xóa Todo (gọi DELETE trả về 403) và KHÔNG THỂ chia sẻ Todo đó cho bên thứ ba.

### User Story 3: Thu hồi quyền
- **As an** Owner
- **I want to** thu hồi quyền truy cập (revoke) của một người đã được chia sẻ
- **So that** họ không thể tiếp tục xem hoặc sửa Todo của tôi nữa.
- **Acceptance Criteria**:
  - [ ] Owner có thể xóa (revoke) quyền của một người dùng bất kỳ.
  - [ ] Ngay lập tức sau khi revoke, hệ thống phải xóa cache Redis liên quan để quyền truy cập bị chặn ngay (Immediate cache invalidation).

## 3. Scope
- **In-Scope**: 
  - API chia sẻ Todo theo từng cá nhân (1 Todo share cho 1 User lúc này).
  - Phân quyền theo 2 cấp: `viewer` và `editor`.
  - Quyền truy cập API: GET và PUT dựa trên phân quyền.
  - API thu hồi quyền.
- **Out-of-Scope**:
  - Tính năng gửi Email Notification / In-app Notification khi được chia sẻ (để tránh scope creep).
  - Chia sẻ Todo cho một Group/Team.
  - Share bằng Public Link (chỉ hỗ trợ user nội bộ).
  - Khả năng Edit đồng thời kiểu Real-time (sẽ dựa vào Optimistic Locking hoặc "Last write wins").

## 4. Database Design

- **New Table**: `todo_shares`
  - `id`: UUID (Primary Key)
  - `todo_id`: UUID (Foreign Key trỏ tới `todos.id`, `ON DELETE CASCADE`)
  - `shared_with_user_id`: UUID (Foreign Key trỏ tới `users.id`, `ON DELETE CASCADE`)
  - `permission_level`: String/Enum (`viewer`, `editor`)
  - `created_at`: TIMESTAMP
  - `updated_at`: TIMESTAMP

- **Constraints & Indexes**:
  - **Unique Constraint**: `UNIQUE(todo_id, shared_with_user_id)` để đảm bảo một người không bị nhận lời mời nhiều lần cho cùng một Todo.
  - **Index**: 
    - `INDEX(shared_with_user_id)` để tăng tốc độ truy vấn danh sách Todos "Được chia sẻ với tôi".
    - `INDEX(todo_id)` để dễ dàng lấy danh sách người đang được chia sẻ đối với Todo hiện hành.
  - **Cascade Delete**: Khi Todo bị xóa, tất cả các record trong `todo_shares` liên kết sẽ bị xóa tự động. Tương tự khi một User bị xóa, các quyền được chia sẻ cho họ cũng biến mất.

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todos/{id}/share` | Chia sẻ Todo cho người dùng khác | Yes (Chỉ Owner) |
| GET | `/api/v1/todos/shared` | Lấy danh sách Todos được chia sẻ với Current User | Yes |
| DELETE | `/api/v1/todos/{id}/share/{user_id}`| Thu hồi quyền của một người | Yes (Chỉ Owner) |

### 5.1 POST `/api/v1/todos/{id}/share`
- **Request Body**:
  ```json
  {
    "email": "collaborator@example.com",
    "permission_level": "viewer" // hoặc "editor"
  }
  ```
- **Responses**:
  - `201 Created`: Thành công.
  - `400 Bad Request`: `Cannot share with yourself.`
  - `403 Forbidden`: User hiện tại không phải Owner của Todo này.
  - `404 Not Found`: Todo không tồn tại, hoặc Email người được share không tồn tại.
  - `409 Conflict`: `User has already been granted access to this todo.`

## 6. Business Logic & Security Considerations

- **Authorization & Permission Matrix**:
  - Chủ sở hữu (Owner): Đọc, Sửa, Xóa, Chia sẻ, Thu hồi.
  - Editor: Đọc, Sửa.
  - Viewer: Đọc.
  - Ngăn chặn chia sẻ tiếp nối: Collaborator (Viewer/Editor) gọi API `/share` sẽ bị chặn (HTTP 403). Chỉ Owner mới có thể kiểm soát danh sách người được share.

- **Edge Cases & Race Conditions**:
  - **Tự chia sẻ (Self-sharing)**: API sẽ validate nếu `email` gửi lên bằng với `current_user.email` thì trả về lỗi 400.
  - **Thu hồi khi đang sửa (Concurrent Revocation)**: Nếu Owner thu hồi quyền trong lúc Editor đang điền dở Form và bấm Submit, API update của Editor sẽ nhận lỗi 403 ngay lập tức do hệ thống lấy quyền trực tiếp từ Database hoặc Cache đã được Invalidate.
  - **Concurrent Updates (Tranh chấp ghi)**: Nếu Owner và Editor cùng lưu Todo một lúc, áp dụng chiến thuật "Last write wins" (đơn giản) hoặc Optimistic Locking (dùng version/timestamp) để tránh ghi đè sai sót.

## 7. Caching & Invalidation Strategy
- Dữ liệu `todo_shares` sẽ không cache toàn bộ mà sẽ được tích hợp vào logic kiểm tra Authorization ở mỗi request (hoặc cache tạm thời trong 5 phút theo định dạng Key: `todo:{id}:shares`).
- **Cache Invalidation**:
  - **Khi Owner gọi `/share` hoặc xóa Share (revoke)**: Xóa (invalidate) key Redis chứa thông tin của Todo hiện tại: `DEL todo:{id}` và `DEL todo:{id}:shares`.
  - **Sự cố độ trễ (Stale Data)**: Việc revoke phải đảm bảo tính tức thời. Cache phải bị Invalidate **ngay trong cùng transaction hoặc hàm thực thi API DELETE /share**, chặn đứng toàn bộ mọi API request tiếp theo đến từ User vừa bị revoke.
