# Manual Test Plan: Tier 2 Testing Strategy

## 1. Scope & Objective
- Mục tiêu kiểm thử: Xác thực các tính năng mới và kiểm tra hồi quy (regression) các lỗi bảo mật và logic đã được khắc phục ở Tier 1.
- Phạm vi kiểm thử: Authentication (Xác thực JWT), Todo CRUD, Authorization (Phân quyền sở hữu), và Caching (Đồng bộ bộ nhớ đệm).

## 2. Test Environment & Prerequisites
- Base URL Backend: `http://localhost:8000`
- Base URL Frontend: `http://localhost:3000`
- Pre-seeded Test Accounts:
  - Account 1 (User A): `user_a@test.com` / `Password@123`
  - Account 2 (User B): `user_b@test.com` / `Password@123`

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status (Pass/Fail) |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Login thành công với mật khẩu đúng | User đã đăng ký | 1. Nhập email/pass đúng<br>2. Bấm Login | Trả về token, chuyển hướng vào Todo page | High / Blocker | |
| TC-02 | Auth | Login thất bại với mật khẩu sai (Tránh User Enumeration) | User đã đăng ký | 1. Nhập email đúng, pass sai<br>2. Bấm Login | Báo lỗi chung "Invalid email or password" (HTTP 401) | Medium / Security | |
| TC-03 | Todo Security | User A không thể sửa hoặc xóa Todo của User B | User A & B đã login | 1. User B tạo todo ID X<br>2. User A gọi PUT /todos/X hoặc DELETE /todos/X | Trả về 403 Forbidden hoặc 404 Not Found (Đã fix lỗi rò rỉ bảo mật) | High / Critical | |
| TC-04 | Todo Logic | Đổi trạng thái todo hoàn thành sang chưa hoàn thành | Todo đang completed | 1. Bấm checkbox bỏ completed<br>2. Refresh trang | Todo vẫn ở trạng thái incomplete (completed = false) | Medium / Major | |
| TC-05 | Cache | Cập nhật Todo xóa cache lập tức | Todo đã được cache | 1. Sửa title Todo<br>2. F5 hoặc gọi GET /todos | Hiển thị title mới, không nhận cache cũ (Đã fix lỗi thiếu Invalidation) | Medium / Major | |
| TC-06 | Auth Security| Token hết hạn sẽ bị từ chối | Có sẵn token hết hạn | 1. Gọi API GET /todos với token hết hạn | Trả về lỗi 401 Unauthorized thay vì chấp nhận | High / Critical | |

## 4. Defect Tracking & Known Limitations
- Toàn bộ các lỗ hổng nghiêm trọng đã được vá thành công ở Tier 1.
- Hiện chưa phát hiện ra lỗi mới. Cần tích hợp thêm các bài test E2E để xác nhận tính ổn định của UI.
