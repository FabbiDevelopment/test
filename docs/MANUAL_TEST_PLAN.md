# Manual Test Plan: Full-Stack Todo Application QA & Regression

## 1. Scope & Objective
- **Mục tiêu kiểm thử**: Xác thực chất lượng toàn diện của ứng dụng Todo App (Frontend & Backend), kiểm tra hồi quy (regression) các lỗi bảo mật và logic nghiệp vụ đã được sửa chữa, đảm bảo tính toàn vẹn dữ liệu, phân quyền bảo mật, và tính nhất quán của tầng caching.
- **Phạm vi kiểm thử**:
  - Authentication & Token Management (JWT verification, Expiration, Token Tampering, User Enumeration prevention, Logout data clearing).
  - Authorization & Data Isolation (IDOR prevention, Cross-user isolation).
  - Todo Core CRUD & State Management (Create, Read, Partial Update, Delete, Toggle Complete/Incomplete).
  - Caching & Invalidation (User-scoped Redis caching, Immediate cache eviction on mutations).
  - UI / UX & Optimistic UI (Form reset state, List key stability, Error rollback).

## 2. Test Environment & Prerequisites
- **Base URL Backend**: `http://localhost:8000` (FastAPI Swagger UI: `http://localhost:8000/docs`)
- **Base URL Frontend**: `http://localhost:3000`
- **Database & Cache**: PostgreSQL 16 (Port 5432), Redis 7 (Port 6379)
- **Pre-seeded Test Accounts**:
  - **Account 1 (User A)**: `user_a@test.com` / `Password@123`
  - **Account 2 (User B)**: `user_b@test.com` / `Password@123`
  - **Demo Account**: `demo@test.com` / `Demo@123`

---

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại | 1. Truy cập `/register`<br>2. Nhập email hợp lệ và password khớp confirm<br>3. Bấm "Create Account" | Tạo tài khoản thành công, nhận JWT tokens, tự động chuyển hướng về trang `/` (Todo list) | High / Blocker | PASS |
| **TC-02** | Auth | Đăng ký thất bại khi email đã tồn tại | Email đã có trong hệ thống | 1. Nhập email đã đăng ký<br>2. Bấm "Create Account" | Hiển thị thông báo lỗi "Email already registered" (HTTP 400) | High / Major | PASS |
| **TC-03** | Auth | Login thành công với mật khẩu đúng | User đã đăng ký | 1. Truy cập `/login`<br>2. Nhập đúng email/password<br>3. Bấm "Sign In" | Đăng nhập thành công, lưu token vào localStorage, chuyển hướng vào `/` | High / Blocker | PASS |
| **TC-04** | Auth | Login thất bại không làm lộ người dùng (Anti-Enumeration) | Hệ thống đang chạy | 1. Nhập email không tồn tại hoặc sai password<br>2. Bấm "Sign In" | Báo lỗi chung "Incorrect email or password" (HTTP 401), không phân biệt lỗi email hay password | High / Security | PASS |
| **TC-05** | Auth / Token | Từ chối truy cập khi Access Token hết hạn | Token đã hết hạn | 1. Gửi request kèm access token đã quá hạn | Backend trả về HTTP 401 Unauthorized; Frontend chuyển hướng về `/login` | High / Critical | PASS |
| **TC-06** | Auth / Token | Từ chối truy cập khi JWT Token bị làm giả / sửa đổi | Token bị can thiệp | 1. Gửi request với Bearer token giả mạo | Backend trả về HTTP 401 Unauthorized | High / Security | PASS |
| **TC-07** | Auth / UI | Xóa sạch dữ liệu bộ nhớ đệm khi Logout | Đang đăng nhập và đã load danh sách Todos | 1. Bấm nút "Logout" ở header | Xóa token trong localStorage, gọi `queryClient.clear()`, chuyển hướng về `/login`. User khác login trên cùng trình duyệt không thấy dữ liệu cũ | High / Security | PASS |
| **TC-08** | Todo CRUD | Tạo mới Todo thành công | Đã đăng nhập | 1. Bấm "Add Todo"<br>2. Nhập Title & Description<br>3. Bấm "Create" | Modal đóng lại, Todo mới xuất hiện ngay trên đầu danh sách với completed = false | High / Blocker | PASS |
| **TC-09** | Todo CRUD | Cập nhật một phần (Partial Update) không mất description | Todo đã tồn tại có description | 1. Bấm nút Edit trên Todo<br>2. Chỉ đổi Title, giữ nguyên description<br>3. Bấm "Save" | Title được cập nhật mới, description ban đầu vẫn giữ nguyên vẹn | High / Major | PASS |
| **TC-10** | Todo CRUD | Toggle hoàn thành (True -> False và ngược lại) | Todo đang ở trạng thái completed = true | 1. Bấm bỏ chọn checkbox của Todo đã hoàn thành<br>2. F5 hoặc tải lại trang | Checkbox hiển thị unchecked, gạch ngang biến mất, completed = false được lưu bền vững vào DB | High / Critical | PASS |
| **TC-11** | Todo CRUD | Xóa Todo thành công | Todo thuộc sở hữu của user | 1. Bấm nút xóa (Trash icon) trên Todo | Todo biến mất khỏi UI và DB, cache được cập nhật | Medium / Major | PASS |
| **TC-12** | Authorization | User A không thể đọc Todo của User B (IDOR Check) | User A & B đã tạo todo riêng | 1. User B tạo todo có ID = `X`<br>2. User A gọi `GET /api/v1/todos/X` | Trả về HTTP 404 Not Found (Data Isolation) | Critical / Blocker | PASS |
| **TC-13** | Authorization | User A không thể sửa/xóa Todo của User B | User A & B đã login | 1. User A gọi `PUT /api/v1/todos/X` hoặc `DELETE /api/v1/todos/X` | Trả về HTTP 404 Not Found, dữ liệu của User B không bị ảnh hưởng | Critical / Blocker | PASS |
| **TC-14** | Cache | Danh sách Todo được phân lập cache theo từng User | User A & User B cùng truy cập | 1. User A load danh sách todos (cache lưu)<br>2. User B load danh sách todos | User B nhận danh sách của User B, không bị nhận nhầm cache của User A | Critical / Security | PASS |
| **TC-15** | Cache | Invalidate cache ngay lập tức khi Create / Update / Delete | Danh sách đã được cache Redis | 1. User tạo/sửa/xóa todo<br>2. Gọi lại `GET /api/v1/todos` | Dữ liệu mới nhất được trả về từ DB và cache lại key mới, không bị lưu dữ liệu cũ | High / Major | PASS |
| **TC-16** | Frontend UI | Form Edit hiển thị đúng dữ liệu của Todo được chọn | Có nhiều Todo trong danh sách | 1. Bấm Edit Todo 1 -> Cancel<br>2. Bấm Edit Todo 2 | Modal hiển thị đúng tiêu đề và mô tả của Todo 2 (form state sync) | Medium / UI | PASS |

---

## 4. Defect Tracking & Known Limitations
1. **Lỗi đã xử lý (Resolved)**:
   - Đã bật kiểm tra hạn JWT trong `backend/app/core/security.py`.
   - Đã bảo vệ các endpoint CRUD Todo theo `current_user.id` (ngăn chặn IDOR).
   - Đã phân lập Redis cache key theo user (`todos:user:{user_id}:*`) và hỗ trợ xóa cache hàng loạt theo pattern.
   - Đã sửa lỗi logic `completed=False` trong API update Todo.
   - Đã khắc phục rò rỉ dữ liệu React Query khi logout trên Frontend.
   - Đã chuẩn hóa response đăng nhập thất bại để chống User Enumeration.
2. **Khuyến nghị mở rộng tương lai**:
   - Thêm rate limiting cho endpoint `/login` và `/register` bằng Redis Token Bucket để chống tấn công brute-force.
   - Bổ sung Refresh Token Blacklisting khi người dùng chủ động Logout.
