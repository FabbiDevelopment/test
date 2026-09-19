# Manual Test Plan: Authentication, Todo CRUD, Security & Caching Regression

## 1. Scope & Objective
- Mục tiêu kiểm thử: 
  - Xác thực các luồng nghiệp vụ cốt lõi (Authentication, Todo CRUD).
  - Kiểm thử hồi quy (Regression Testing) nhằm đảm bảo 7 lỗi nghiêm trọng đã được sửa ở Tier 1 (Security, Cache Invalidation, Logic Boolean, Partial Update, Logout Cleanup) không bị tái phát.
  - Đảm bảo tính toàn vẹn dữ liệu, bảo mật phân quyền đa người dùng (IDOR) và hiệu năng bộ nhớ đệm (Redis Cache)

- Phạm vi kiểm thử:
  - **Module Auth:** Register, Login, Token Expiry, Logout.
  - **Module Todo CRUD & Logic:** Create, Read, Partial Update, Boolean Toggle, Delete.
  - **Module Security (Authorization):** IDOR Prevention, Cross-user Data Isolation.
  - **Module Caching & Performance:** Cache Hit/Miss, Invalidation on Mutation, N+1 Query Prevention.


## 2. Test Environment & Prerequisites
- Backend API URL: `http://localhost:8000` (Swagger UI: `http://localhost:8000/docs`)
- Frontend URL: `http://localhost:5173`
- Database & Cache: PostgreSQL 16 (`localhost:5432`), Redis 7 (`localhost:6379`)
- Pre-seeded Test Accounts:
  - User A: `user_a@example.com` / `Password@123`
  - User B: `user_b@example.com` / `Password@123`

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
| TC-01 | Auth | Đăng nhập thành công với thông tin hợp lệ | User đã đăng ký trong DB | 1. Mở `/login`<br>2. Nhập email/password hợp lệ<br>3. Bấm "Sign In" | Đăng nhập thành công, nhận JWT Token, chuyển hướng vào `/` (Dashboard Todo) | High / Blocker | **PASS** |
| TC-02 | Auth (Security) | Đăng nhập thất bại với sai mật khẩu (Chống User Enumeration) | User đã đăng ký | 1. Mở `/login`<br>2. Nhập đúng email, sai password<br>3. Bấm "Sign In" | Báo lỗi chung `"Invalid email or password"` (HTTP 401), không để lộ việc email có tồn tại hay không | Medium / Security | **PASS** |
| **TC-03** | Auth (Security) | Từ chối truy cập khi Access Token hết hạn (BUG-B01 Regression) | Token đã hết hạn (`exp` trong quá khứ) | 1. Gửi request kèm Bearer token hết hạn lên `/api/v1/auth/me` hoặc `/api/v1/todos` | Backend trả về `401 Unauthorized`. Frontend tự động redirect về `/login` | High / Critical | **PASS** |
| **TC-04** | Auth (Session) | Đăng xuất làm sạch toàn bộ Cache phía Client (BUG-F01 Regression) | User A đang đăng nhập và có danh sách Todo trên màn hình | 1. Bấm nút "Logout"<br>2. Đăng nhập bằng tài khoản User B | `queryClient` được clear toàn bộ. User B không thấy bất kỳ Todo nào của User A trên UI | High / Major | **PASS** |
| **TC-05** | Todo (Logic) | Chuyển đổi trạng thái từ hoàn thành (`true`) về chưa hoàn thành (`false`) (BUG-B05 Regression) | Todo đang có `completed: true` | 1. Bấm checkbox để bỏ hoàn thành (`completed: false`)<br>2. Refresh lại trang (F5) | Todo vẫn duy trì trạng thái chưa hoàn thành (`completed: false`, không gạch ngang) | Medium / Major | **PASS** |
| **TC-06** | Todo (Logic) | Cập nhật một phần (Partial Update) giữ nguyên Description (BUG-B06 Regression) | Todo có title "Task 1", description "Chi tiết 1" | 1. Gửi request `PUT /todos/{id}` với payload chỉ có `{"title": "Task 1 mới"}` | Title đổi thành "Task 1 mới", `description` vẫn giữ nguyên là "Chi tiết 1" (không bị null) | Medium / Major | **PASS** |
| **TC-07** | Security (IDOR) | Ngăn chặn User A sửa hoặc xóa Todo của User B (BUG-B03 Regression) | User A & B đã tạo Todo riêng; User A biết ID Todo của B | 1. User A gửi `PUT /todos/{todo_b_id}`<br>2. User A gửi `DELETE /todos/{todo_b_id}` | Backend từ chối với `403 Forbidden` (hoặc `404 Not Found`). Dữ liệu User B không bị thay đổi | High / Critical | **PASS** |
| **TC-08** | Security (Data Isolation) | User B không thể đọc Todo của User A (BUG-B02 Regression) | User A đã tạo Todo bí mật X | 1. User B đăng nhập vào hệ thống<br>2. Gọi `GET /todos` | Danh sách trả về chỉ chứa Todo của User B. Tuyệt đối không có Todo X của User A | High / Critical | **PASS** |
| **TC-09** | Cache (Consistency) | Cache bị vô hiệu hóa (Invalidate) ngay khi có thay đổi dữ liệu | Danh sách Todo đã được lưu cache trong Redis | 1. Tạo mới / Sửa / Xóa một Todo<br>2. Gọi lại `GET /todos` ngay lập tức | Cache cũ bị xóa. Dữ liệu mới nhất từ DB được trả về và cập nhật lại vào cache mới | Medium / Major | **PASS** |
| **TC-10** | Performance | Tránh truy vấn N+1 khi lấy danh sách Todo (BUG-B04 Regression) | User có 20 Todos | 1. Gọi `GET /todos`<br>2. Quan sát log truy vấn SQL | Chỉ thực thi 1 query lấy todos + 1 query đếm (count), không phát sinh 20 query lặp để lấy email | Low / Minor | **PASS** |



## 4. Defect Tracking & Regression Verification Summary

- Toàn bộ các lỗi phát hiện tại Tier 1 đã được xác minh kiểm thử thành công qua cả 2 phương pháp:
1. **Automated Backend Pytest:** 13/13 tests passed (`pytest tests/ -v`).
2. **Automated E2E Playwright:** 2/2 scenarios passed (`npx playwright test`).

| Defect ID | Mô tả lỗi ban đầu | Mức độ | Trạng thái sau sửa | Minh chứng kiểm thử |
|---|---|---|---|---|
| **BUG-B01** | Bỏ qua kiểm tra hạn token (`verify_exp: False`) | Critical | Fixed | `test_expired_token_rejection` (PASSED) |
| **BUG-B02** | Redis Cache dùng chung key không cô lập theo user | Critical | Fixed | `Scenario 2: Cross-User Data Isolation` (PASSED) |
| **BUG-B03** | Lỗ hổng IDOR cho phép sửa/xóa Todo người khác | Critical | Fixed | `test_cross_user_authorization_boundary` (PASSED) |
| **BUG-B04** | N+1 Query lặp lại khi lấy email người dùng | Medium | Fixed | Gán trực tiếp `user_email=current_user.email` |
| **BUG-B05** | Không thể đổi completed từ `true` về `false` | High | Fixed | `test_boolean_toggle_completed_to_false` (PASSED) |
| **BUG-B06** | Cập nhật partial làm ghi đè mất description | Medium | Fixed | `test_partial_update_preserves_description` (PASSED) |
| **BUG-F01** | Frontend không xóa cache React Query khi Logout | High | Fixed | `useAuth.ts: queryClient.clear()` |

