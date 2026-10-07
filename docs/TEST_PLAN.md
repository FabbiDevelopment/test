# Manual Test Plan: Full-Stack Regression & Security Scope

## 1. Scope & Objective
- **Mục tiêu kiểm thử**: Xác thực chất lượng toàn diện của ứng dụng Todo, kiểm tra hồi quy (regression) các lỗi nghiệp vụ đã sửa, và xác nhận tính toàn vẹn bảo mật (Authentication, Authorization, Data Isolation, Caching).
- **Phạm vi kiểm thử**:
  - Authentication & Token Lifecycle (Register, Login, Expiration, Type Validation).
  - Todo CRUD & Data Persistence (Create, Read, Partial Update, Boolean Toggle, Delete).
  - Cross-User Authorization Boundary (IDOR / Data Isolation).
  - Performance & Redis Caching Layer.

## 2. Test Environment & Prerequisites
- **Base URL Backend**: `http://localhost:8000`
- **Base URL Frontend**: `http://localhost:3000`
- **Pre-seeded / Test Accounts**:
  - Account 1 (User A): `user_a@test.com` / `Password@123`
  - Account 2 (User B): `user_b@test.com` / `Password@123`

---

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại | 1. Nhập email hợp lệ<br>2. Nhập mật khẩu hợp lệ<br>3. Bấm Register | Trả về 201 Created + Token, lưu token vào LocalStorage | High / Blocker | **PASS** |
| **TC-02** | Auth | Ngăn chặn tạo tài khoản trùng email (Data Integrity) | Email đã tồn tại | 1. Đăng ký lại với email đã có trong hệ thống<br>2. Bấm Register | Trả về HTTP 400 Bad Request: "Email already registered" | High / Critical | **PASS** |
| **TC-03** | Auth | Chặn Token đã hết hạn (JWT Expiration) | Token đã hết hạn | 1. Dùng token hết hạn gọi GET /api/v1/auth/me | Trả về HTTP 401 Unauthorized, không cho truy cập | High / Critical | **PASS** |
| **TC-04** | Auth | Chặn dùng Refresh Token thay Access Token (Token Type) | Có refresh_token hợp lệ | 1. Gửi refresh_token vào header Authorization gọi GET /me | Trả về HTTP 401 Unauthorized: "Invalid token type" | High / Critical | **PASS** |
| **TC-05** | Todo Logic | Đổi trạng thái todo từ hoàn thành sang chưa hoàn thành (Boolean Toggle) | Todo đang completed = True | 1. Bấm checkbox bỏ tick completed<br>2. Refresh trang hoặc gọi GET /todos | Trạng thái completed = False được lưu bền vững vào DB | High / Major | **PASS** |
| **TC-06** | Todo Logic | Cập nhật Title không làm mất Description (Partial Update) | Todo đã có description | 1. Gọi PUT /todos/{id} chỉ gửi `{ "title": "New Title" }`<br>2. Kiểm tra lại Todo | Title đổi mới, Description cũ vẫn được giữ nguyên vẹn | High / Major | **PASS** |
| **TC-07** | Todo Security | User A không thể xem, sửa hoặc xóa Todo của User B (IDOR Isolation) | User A và B đều đã đăng nhập | 1. User B tạo Todo ID X<br>2. User A gọi GET/PUT/DELETE /todos/X | Trả về HTTP 404 Not Found, bảo vệ tuyệt đối dữ liệu cá nhân | Critical / Blocker | **PASS** |
| **TC-08** | Performance | Lấy danh sách Todo không bị lỗi N+1 Query | User có nhiều Todo | 1. Gọi GET /api/v1/todos<br>2. Giám sát số lượng câu query DB | Chỉ thực hiện 1 truy vấn SELECT Todos, map email từ context | Medium / Performance | **PASS** |
| **TC-09** | Redis Cache | Cô lập Cache Todo giữa các người dùng (Cache Key Scoping) | User A & B có danh sách Todo khác nhau | 1. User A gọi GET /todos (ghi cache)<br>2. User B gọi GET /todos | User B không nhìn thấy cache của User A; Cache phân tách theo user_id | High / Critical | **PASS** |
| **TC-10** | Frontend UI | Render danh sách Todo ổn định khi thay đổi thứ tự (React Key) | Danh sách có nhiều Todo | 1. Thêm / Xóa / Hoàn thành các Todo liên tiếp | Không có cảnh báo console về React key, state UI không bị nhảy loạn | Low / Minor | **PASS** |

---

## 4. Defect Tracking & Known Limitations
- **Lỗi đã xử lý**: Tất cả 10 lỗi trọng yếu thuộc Authentication, Data Integrity, Authorization IDOR, Business Logic và Redis Performance đều đã được vá triệt để và phủ automated test (100% PASS).
- **Phạm vi mở rộng (Next release)**: Tính năng chia sẻ danh sách Todo giữa nhiều người dùng (sẽ được thiết kế trong tài liệu `docs/TODO_SHARING_SPEC.md`).
