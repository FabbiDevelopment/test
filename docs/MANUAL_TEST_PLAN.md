# Manual Test Plan: Authentication, Authorization & Todo CRUD

## 1. Scope & Objective

- **Mục tiêu kiểm thử**: Xác thực các bug đã fix ở Tier 1 không tái xuất hiện (regression), và kiểm tra các luồng chính chưa được cover đầy đủ bởi automated test (pytest/Playwright).
- **Phạm vi kiểm thử**: Authentication (JWT, token type), Authorization (IDOR, cross-user isolation), Todo CRUD logic, Redis Caching, Session handling.
- **Ngoài phạm vi**: Load testing, penetration testing chuyên sâu, cross-browser compatibility (chỉ test trên Chrome).

## 2. Test Environment & Prerequisites

- Base URL Backend: `http://localhost:8000`
- Base URL Frontend: `http://localhost:3000`
- Stack chạy qua: `docker-compose up --build -d` (đảm bảo rebuild mới nhất trước khi test)
- Pre-seeded Test Accounts:
  - Demo Account: `demo@test.com` / `Demo@123`
  - Account 1 (User A): tạo mới qua `/register` lúc test, ví dụ `user_a@test.com` / `Password@123`
  - Account 2 (User B): tạo mới qua `/register` lúc test, ví dụ `user_b@test.com` / `Password@123`

## 3. Test Cases Matrix

| TC ID | Module | Test Scenario | Preconditions | Test Steps | Expected Result | Priority/Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Login thành công với mật khẩu đúng | User đã đăng ký | 1. Nhập email/pass đúng<br>2. Bấm "Sign In" | Redirect vào Dashboard, `access_token` lưu trong localStorage | High / Blocker | |
| TC-02 | Auth | Login thất bại với mật khẩu sai | User đã đăng ký | 1. Nhập email đúng, pass sai<br>2. Bấm "Sign In" | Toast báo lỗi, không redirect, không lưu token | Medium / Major | |
| TC-03 | Auth | Đăng ký với email đã tồn tại | Email đã có tài khoản | 1. Vào `/register`<br>2. Nhập email trùng<br>3. Submit | Báo lỗi rõ ràng (không tạo user trùng, không crash 500) | Medium / Major | |
| TC-04 | Auth | Token hết hạn bị từ chối | User đã login >30 phút (hoặc token giả lập hết hạn) | 1. Gọi bất kỳ API cần auth với token cũ | Trả về 401, frontend redirect về `/login` | High / Critical (Bug 1 regression) | |
| TC-05 | Auth | Refresh token không dùng được như access token | User đã login, có refresh_token | 1. Copy refresh_token<br>2. Gọi `GET /api/v1/auth/me` với Bearer = refresh_token | Trả về 401 "Invalid token type" | High / Critical (Bug 7 regression) | |
| TC-06 | Auth | Logout xóa sạch session | User đã login, có todos hiển thị | 1. Bấm "Logout"<br>2. Kiểm tra localStorage | Token bị xóa, redirect về `/login`, không truy cập được Dashboard nếu back lại | High / Major | |
| TC-07 | Authorization | User A không đọc được todo của User B | Cả 2 user đã có todo riêng | 1. User B lấy ID todo của mình<br>2. User A dùng token của mình gọi `GET /todos/{id_B}` | Trả về 404 Not Found | High / Critical (Bug 2 regression) | |
| TC-08 | Authorization | User A không sửa được todo của User B | Như trên | 1. User A gọi `PUT /todos/{id_B}` với body bất kỳ | Trả về 404, dữ liệu todo của B không đổi | High / Critical (Bug 2 regression) | |
| TC-09 | Authorization | User A không xóa được todo của User B | Như trên | 1. User A gọi `DELETE /todos/{id_B}` | Trả về 404, todo của B vẫn còn tồn tại | High / Critical (Bug 2 regression) | |
| TC-10 | Caching | Cache list todo không rò rỉ giữa 2 user | User A vừa GET list (populate cache) | 1. User A gọi `GET /todos` (có todo)<br>2. User B gọi `GET /todos` ngay sau | User B chỉ thấy todo của B, KHÔNG thấy todo của A | High / Critical (Bug 3 regression) | |
| TC-11 | Caching | Cache tự invalidate sau khi tạo todo mới | User đã có ≥1 todo, đã GET list 1 lần | 1. Tạo thêm 1 todo mới<br>2. GET list ngay (không F5) | Todo mới xuất hiện ngay lập tức, không cần đợi 5 phút TTL | High / Major (Bug 4 regression) | |
| TC-12 | Todo Logic | Toggle completed true→false lưu đúng | Todo đang `completed = true` | 1. Bấm checkbox bỏ completed<br>2. F5 lại trang | Todo vẫn hiển thị chưa hoàn thành sau khi F5 | Medium / Major (Bug 5 regression) | |
| TC-13 | Todo Logic | Partial update giữ nguyên description | Todo có sẵn description | 1. Chỉ sửa title (không đụng description)<br>2. Save<br>3. Mở lại xem chi tiết | Description gốc vẫn còn nguyên, không bị mất | Medium / Major (Bug 6 regression) | |
| TC-14 | Todo Logic | Tạo todo với title rỗng bị chặn | — | 1. Mở dialog "Add Todo"<br>2. Để trống title<br>3. Bấm "Create" | Form hiển thị lỗi validation, không gọi API, không tạo todo rỗng | Low / Minor | |
| TC-15 | Todo Logic | Tạo todo với title vượt quá 200 ký tự | — | 1. Nhập title 250 ký tự<br>2. Submit | Bị chặn ở validation (client hoặc trả 422 từ server) | Low / Minor | |
| TC-16 | Todo Logic | Title chứa ký tự đặc biệt/HTML không gây XSS | — | 1. Tạo todo với title `<script>alert(1)</script>` | Title hiển thị dưới dạng text thuần (escaped), không thực thi script | Medium / Security | |
| TC-17 | Session | Nhiều tab cùng 1 user đồng bộ trạng thái | User login ở 2 tab | 1. Tab 1: tạo todo mới<br>2. Tab 2: F5 | Tab 2 thấy todo mới sau F5 (không bắt buộc real-time, nhưng phải đồng bộ khi reload) | Low / Minor | |
| TC-18 | Session | Truy cập Dashboard khi chưa login | Chưa có token trong localStorage | 1. Vào thẳng `http://localhost:3000/` | Redirect về `/login`, không lộ dữ liệu | High / Critical | |
| TC-19 | Pagination | Danh sách todo trả đúng khi vượt quá 1 trang | User có > `size` mặc định todos | 1. Tạo > 20 todos<br>2. Gọi `GET /todos?page=2&size=20` | Trả về đúng batch tiếp theo, không trùng/thiếu item | Medium / Major | |
| TC-20 | Infra | Backend tự phục hồi khi Postgres khởi động chậm | Cold boot toàn bộ stack | 1. `docker-compose down`<br>2. `docker-compose up --build` | Backend không crash, tự đợi Postgres healthy rồi mới chạy migration | Medium / Major (Docker healthcheck regression) | |

## 4. Defect Tracking & Known Limitations

- **Đã fix và cover bởi automated test**: Bug 1-6 (xem Tier 1 + Tier 2A). TC-04, 05, 07-13 là regression check thủ công bổ sung, không thay thế pytest.
- **Chưa có automated test, chỉ cover bằng manual (TC-14 đến TC-19)**: các case validation/UX chưa nằm trong 5 scenario bắt buộc của Tier 2A.
- **Known limitation chưa fix trong scope bài test này**:
  - Không có rate limiting cho endpoint `/auth/login` → dễ bị brute-force (ngoài phạm vi Tier 1-3 được giao).
  - Không có email verification khi đăng ký.
  - Logout hiện tại không revoke token ở phía server (do JWT stateless) — chỉ xóa token phía client, nếu token bị đánh cắp trước đó vẫn có hiệu lực tới khi hết hạn tự nhiên.