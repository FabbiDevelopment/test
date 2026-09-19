# Technical Specification: Todo List Sharing

## 1. Overview & Objective

- **Feature Summary**: Cho phép chủ sở hữu (owner) của 1 todo chia sẻ quyền xem hoặc chỉnh sửa todo đó cho người dùng khác trong hệ thống, và có thể thu hồi quyền bất kỳ lúc nào.
- **Problem Statement**: Hiện tại mỗi todo chỉ thuộc về đúng 1 user (`todos.user_id`), không có cách nào để cộng tác trên cùng 1 todo giữa nhiều người dùng.
- **Target Audience / Roles**:
  - **Owner**: Người tạo todo, có toàn quyền (đọc/sửa/xóa/chia sẻ/thu hồi quyền).
  - **Editor**: Người được chia sẻ quyền chỉnh sửa (đọc + sửa nội dung, KHÔNG được xóa hay chia sẻ tiếp).
  - **Viewer**: Người được chia sẻ quyền chỉ đọc.

## 2. User Stories & Acceptance Criteria

### User Story 1: Owner chia sẻ todo cho người khác
- **As a** owner của 1 todo
- **I want to** mời 1 user khác (qua email) với quyền viewer hoặc editor
- **So that** chúng tôi có thể cùng theo dõi/cập nhật công việc
- **Acceptance Criteria**:
  - [ ] Owner nhập email người nhận + chọn role (viewer/editor)
  - [ ] Nếu email không tồn tại trong hệ thống → trả lỗi rõ ràng, không tạo share ngầm
  - [ ] Nếu đã share với email đó rồi → không tạo bản ghi trùng, trả lỗi "already shared" hoặc update role nếu owner gửi lại với role khác
  - [ ] Owner không thể tự share cho chính mình

### User Story 2: Người được chia sẻ xem/sửa todo
- **As a** editor hoặc viewer được chia sẻ
- **I want to** thấy todo đó xuất hiện trong danh sách "Shared with me"
- **So that** tôi biết mình đang được cộng tác trên todo nào
- **Acceptance Criteria**:
  - [ ] Viewer chỉ GET được, gọi PUT/DELETE bị từ chối (403)
  - [ ] Editor GET và PUT được, DELETE bị từ chối (403) — chỉ owner mới xóa được
  - [ ] Cả viewer/editor đều KHÔNG thấy nút "Share" (không được chia sẻ tiếp)

### User Story 3: Owner thu hồi quyền
- **As a** owner
- **I want to** thu hồi quyền truy cập của 1 người bất kỳ lúc nào
- **So that** tôi kiểm soát được ai đang có quyền trên todo của mình
- **Acceptance Criteria**:
  - [ ] Sau khi thu hồi, người bị thu hồi gọi GET/PUT todo đó phải nhận 404 ngay lập tức (không có độ trễ do cache cũ)
  - [ ] Thu hồi quyền không xóa todo, chỉ xóa bản ghi chia sẻ

## 3. Scope

- **In-Scope**:
  - Share/unshare 1 todo cho nhiều user với 2 role: viewer, editor
  - Danh sách "Shared with me" và "People with access" (cho owner xem ai đang có quyền)
  - Cache invalidation đúng khi share/unshare
- **Out-of-Scope** (để tránh scope creep):
  - Share cả 1 danh sách/folder todo cùng lúc (chỉ share từng todo riêng lẻ)
  - Real-time collaborative editing (WebSocket, conflict resolution kiểu Google Docs)
  - Notification/email khi được share
  - Public share link (share qua URL công khai không cần tài khoản)
  - Phân quyền theo nhóm (team/organization)

## 4. Database Design

### Bảng mới: `todo_shares`

| Column | Type | Constraint |
|---|---|---|
| `id` | UUID | Primary Key, default `gen_random_uuid()` |
| `todo_id` | UUID | Foreign Key → `todos.id`, `ON DELETE CASCADE` |
| `shared_with_user_id` | UUID | Foreign Key → `users.id`, `ON DELETE CASCADE` |
| `role` | ENUM(`viewer`, `editor`) | NOT NULL |
| `shared_by_user_id` | UUID | Foreign Key → `users.id` (owner tại thời điểm share) |
| `created_at` | TIMESTAMP WITH TIME ZONE | NOT NULL, default `now()` |

**Constraints & Indexes**:
- `UNIQUE (todo_id, shared_with_user_id)` — 1 user chỉ có đúng 1 bản ghi share cho 1 todo (tránh duplicate invite; nếu share lại thì `UPDATE role` thay vì insert mới).
- Index trên `(shared_with_user_id)` — phục vụ query "Shared with me" nhanh.
- Index trên `(todo_id)` — phục vụ query "People with access" nhanh.
- `ON DELETE CASCADE` ở cả 2 FK: nếu todo bị xóa hoặc user bị xóa, các bản ghi share liên quan tự động dọn theo, không để rác.
- Ràng buộc ở tầng application (không đủ diễn đạt bằng DB constraint thuần): `shared_with_user_id != (SELECT user_id FROM todos WHERE id = todo_id)` — chặn tự share cho chính mình, check ở service layer trước khi insert.

## 5. API Contracts & Endpoints

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| POST | `/api/v1/todos/{todo_id}/shares` | Owner chia sẻ todo cho 1 user | Yes (owner only) |
| GET | `/api/v1/todos/{todo_id}/shares` | Owner xem danh sách người đang có quyền | Yes (owner only) |
| PATCH | `/api/v1/todos/{todo_id}/shares/{share_id}` | Owner đổi role (viewer↔editor) | Yes (owner only) |
| DELETE | `/api/v1/todos/{todo_id}/shares/{share_id}` | Owner thu hồi quyền của 1 người | Yes (owner only) |
| GET | `/api/v1/todos/shared-with-me` | User xem danh sách todo được chia sẻ cho mình | Yes |

**Request Body — POST `/shares`**:
```json
{
  "email": "collaborator@example.com",
  "role": "editor"
}
```

**Response codes**:
- `201 Created` — share thành công, trả về `TodoShareResponse`
- `400 Bad Request` — `role` không hợp lệ (không phải viewer/editor), hoặc tự share cho chính mình
- `403 Forbidden` — người gọi không phải owner của todo
- `404 Not Found` — todo không tồn tại (hoặc không thuộc về người gọi — dùng 404 thay vì 403 để tránh lộ thông tin, nhất quán với cách xử lý IDOR đã áp dụng ở phần CRUD todo cơ bản), hoặc email người nhận không tồn tại trong hệ thống
- `409 Conflict` — đã share với email này rồi (gợi ý dùng PATCH để đổi role thay vì tạo mới)

## 6. Business Logic & Security Considerations

### Authorization & Permission Matrix

| Action | Owner | Editor | Viewer | Người khác (chưa share) |
|---|---|---|---|---|
| GET todo | ✅ | ✅ | ✅ | ❌ (404) |
| PUT todo (sửa nội dung) | ✅ | ✅ | ❌ (403) | ❌ (404) |
| DELETE todo | ✅ | ❌ (403) | ❌ (403) | ❌ (404) |
| POST share (mời người mới) | ✅ | ❌ (403) | ❌ (403) | ❌ (404) |
| DELETE share (thu hồi quyền) | ✅ | ❌ (403) | ❌ (403) | ❌ (404) |

Quy tắc nền tảng khi check quyền ở mọi endpoint todo hiện có (`GET/PUT/DELETE /todos/{id}`): thay vì chỉ check `todo.user_id == current_user.id` như hiện tại, mở rộng logic thành "user là owner HOẶC có bản ghi active trong `todo_shares`", kèm kiểm tra `role` tương ứng với hành động (viewer chỉ qua được GET, editor qua được GET+PUT).

### Edge Cases & Race Conditions

- **Mời trùng lặp**: nhờ `UNIQUE (todo_id, shared_with_user_id)`, insert trùng sẽ bị DB reject → API trả `409 Conflict`, gợi ý dùng PATCH để update role thay vì lỗi mơ hồ.
- **User tự share cho chính mình**: check ở service layer trước khi insert — `shared_with_user_id == todo.user_id` → trả `400 Bad Request`.
- **Owner thu hồi quyền trong lúc collaborator đang PUT**: dùng transaction — nếu request PUT của collaborator đến sau khi bản ghi share đã bị xóa (dù chỉ vài mili giây), authorization check (query lại DB, không dựa vào cache quyền) sẽ trả 403/404 ngay, không có "grace period" cho request đang bay.
- **Email người được mời chưa có tài khoản**: hệ thống hiện tại không tự tạo tài khoản hộ (out of scope gửi email mời đăng ký) → trả `404 Not Found` với message rõ ràng "User with this email does not exist".
- **Owner xóa todo trong khi đang có người share**: nhờ `ON DELETE CASCADE`, các bản ghi `todo_shares` tự xóa theo, không để lại rác hoặc lỗi FK.

## 7. Caching & Invalidation Strategy

- **Cấu trúc cache key mới**: các API liên quan tới quyền truy cập của user lên 1 todo cụ thể (`GET /todos/{id}`) cần đổi cache key từ chỉ dựa vào `todo_id` sang có thêm ngữ cảnh quyền, ví dụ: `todo:detail:{todo_id}:{accessor_user_id}` — vì response có thể khác nhau tùy role người xem (ví dụ chỉ owner mới thấy được danh sách người đang share).
- **Khi nào invalidate**:
  - Owner tạo mới 1 share (`POST /shares`) → xóa cache `todo:detail:{todo_id}:{shared_with_user_id}` (nếu có từ trước, trường hợp share lại sau khi từng bị revoke) và cache danh sách `todos:list:{shared_with_user_id}:*` (vì todo giờ xuất hiện thêm trong "Shared with me" của họ).
  - Owner thu hồi quyền (`DELETE /shares/{id}`) → xóa ngay `todo:detail:{todo_id}:{revoked_user_id}` và `todos:list:{revoked_user_id}:*`, đảm bảo người bị thu hồi không còn thấy được todo kể cả từ cache, dù TTL cache (300s) chưa hết — đây là yêu cầu bảo mật cứng, không được có độ trễ.
  - Editor sửa nội dung todo (`PUT /todos/{id}`) → invalidate cache cho MỌI người đang có quyền trên todo đó (owner + tất cả viewer/editor khác), không chỉ riêng người gọi — vì tái sử dụng đúng pattern `delete_pattern` đã có, cần liệt kê tất cả `user_id` liên quan (owner + các `shared_with_user_id` trong bảng `todo_shares`) rồi gọi `delete_pattern` cho từng người.