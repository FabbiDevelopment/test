# Manual Test Plan: Authentication & Authorization

## 1. Scope & Objective
- **Mục tiêu kiểm thử**: Xác thực các tính năng bảo mật (Authentication) và phân quyền (Authorization). Đảm bảo các lỗi ở Tier 1 (IDOR, Expired Token) đã được khắc phục hoàn toàn.
- **Phạm vi kiểm thử**: API Authentication (Login/Register/Logout/Me), Todo CRUD, Authorization rules.

## 2. Test Environment & Prerequisites
- Base URL Backend: `http://localhost:8000/api/v1`
- Base URL Frontend: `http://localhost:3000`
- Công cụ: Postman hoặc trình duyệt Chrome.
- **Pre-seeded Test Accounts**:
  - Account 1 (User A): `usera@test.com` / `Password@123`
  - Account 2 (User B): `userb@test.com` / `Password@123`

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status (Pass/Fail) |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Đăng nhập thất bại chống Enumeration | Đã có tài khoản `demo@test.com` | 1. Nhập email chưa đăng ký<br>2. Bấm Login | Hệ thống báo lỗi "Incorrect email or password", HTTP 401 | Medium / Security | Passed |
| TC-02 | Auth | JWT Token hết hạn bị từ chối | Có token đã hết hạn | 1. Gửi request GET `/auth/me` với Bearer token hết hạn | Hệ thống trả về 401 "Could not validate credentials" | High / Critical | Passed |
| TC-03 | Authorization | Cấm truy cập Todo của người khác (IDOR Check) | User A có Todo ID `X` | 1. Đăng nhập User B<br>2. Gửi request GET `/todos/X` | API trả về 403 Forbidden hoặc 404 Not Found | High / Critical | Passed |
| TC-04 | Authorization | Cấm sửa Todo của người khác | User A có Todo ID `X` | 1. Đăng nhập User B<br>2. Gửi request PUT `/todos/X` | API trả về 403 Forbidden hoặc 404 Not Found | High / Critical | Passed |
| TC-05 | Authorization | Cấm xóa Todo của người khác | User A có Todo ID `X` | 1. Đăng nhập User B<br>2. Gửi request DELETE `/todos/X` | API trả về 403 Forbidden hoặc 404 Not Found | High / Critical | Passed |
| TC-06 | Todo Logic | Hủy bỏ trạng thái hoàn thành | Todo đang ở trạng thái `completed=true` | 1. Bấm checkbox để bỏ hoàn thành<br>2. F5 tải lại trang | Checkbox bị bỏ chọn (completed=false) lưu thành công vào DB | Medium / Major | Passed |
| TC-07 | Cache | Dữ liệu Todo mới nhất luôn hiển thị (Cache Invalidation) | User có 1 Todo | 1. Tạo thêm 1 Todo mới<br>2. F5 tải lại trang | Danh sách hiển thị ngay lập tức 2 Todo, không bị kẹt cache cũ | High / Major | Passed |

## 4. Defect Tracking & Known Limitations
- Tất cả các lỗi nghiêm trọng ở Tier 1 đã được sửa và passed các test cases trên.
