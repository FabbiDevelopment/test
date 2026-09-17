# Manual Test Plan: Full-Stack Todo Application

## 1. Scope & Objective
- **Objective**: Kiểm tra toàn bộ quy trình xác thực (Authentication), phân quyền dữ liệu (Authorization), quản lý công việc (Todo CRUD) và tính đúng đắn của Redis Cache.
- **Phạm vi kiểm thử**: API Endpoints (Postman/Curl) & Giao diện người dùng Frontend (Chrome Browser).

## 2. Test Environment & Prerequisites
- Backend URL: `http://localhost:8000`
- Frontend URL: `http://localhost:3000`
- Accounts:
  - Account A: `user_a@test.com` / `Password@123`
  - Account B: `user_b@test.com` / `Password@123`

---

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Đăng nhập thành công | User A đã tạo | 1. Nhập email/pass đúng<br>2. Bấm Login | Đăng nhập thành công, nhận JWT Token, chuyển hướng tới Dashboard | High / Blocker | PASS |
| TC-02 | Auth Security | Đăng nhập thất bại (Chống User Enumeration) | N/A | 1. Nhập email chưa đăng ký<br>2. Bấm Login | Trả về 401 Unauthorized với thông báo "Invalid email or password" (không báo 404) | High / Critical | PASS |
| TC-03 | JWT Security | Token hết hạn bị từ chối | Token exp hết hạn | 1. Dùng Token hết hạn gọi GET /todos | Trả về 401 Unauthorized "Invalid authentication token" | High / Blocker | PASS |
| TC-04 | Authorization | User A không thể sửa Todo của User B | User B có Todo ID X | 1. User A gửi PUT /todos/X | Trả về 404 Not Found (Ngăn cách ly dữ liệu) | High / Critical | PASS |
| TC-05 | Todo Logic | Sửa completed từ true về false | Todo X đang completed=true | 1. Bấm bỏ chọn completed<br>2. F5 làm mới trang | Todo X duy trì trạng thái completed=false trong DB | Medium / Major | PASS |
| TC-06 | Cache Invalidation | Tạo mới Todo xóa cache ngay lập tức | Cache list đã tồn tại | 1. Tạo Todo Y<br>2. Gọi GET /todos | Hiển thị Todo Y mới ngay lập tức | Medium / Major | PASS |
| TC-07 | Frontend State | Đăng xuất làm sạch Cache React Query | User A đang login | 1. Click Logout<br>2. User B Đăng nhập cùng phiên | Dữ liệu User A hoàn toàn biến mất, chỉ hiển thị dữ liệu User B | High / Major | PASS |
