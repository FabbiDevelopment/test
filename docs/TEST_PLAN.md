# Manual Test Plan: Full-Stack Todo Application Regression & Quality Assurance

## 1. Scope & Objective
- **Mục tiêu kiểm thử**: Xác thực tính năng, bảo mật và kiểm tra hồi quy (regression testing) cho toàn bộ 14 lỗi đã được khắc phục trong Tier 1, bảo đảm hệ thống hoạt động ổn định, an toàn và đúng nghiệp vụ.
- **Phạm vi kiểm thử**:
  - Xác thực & Phân quyền (Authentication & Authorization: JWT, Token Type, User Enumeration, BOLA/IDOR).
  - Nghiệp vụ Todo (CRUD, Boolean Toggle, Partial Update, Deterministic Sorting, Form State Reset).
  - Caching & Hiệu năng (Redis Isolation, Cache Invalidation, N+1 Query).
  - Trải nghiệm giao diện & Khả năng phục hồi (Optimistic Update Rollback, Axios 401 Handling).

## 2. Test Environment & Prerequisites
- **Base URL Backend**: `http://localhost:8000` (FastAPI + PostgreSQL + Redis via Docker)
- **Base URL Frontend**: `http://localhost:3000` (React + Vite + TailwindCSS)
- **Tài khoản kiểm thử định sẵn**:
  - User A: `user_a@test.com` / `Password@123`
  - User B: `user_b@test.com` / `Password@123`
- **Công cụ hỗ trợ**: Chrome DevTools, Postman / cURL.

---

## 3. Test Cases Matrix

| TC ID | Module | Kịch bản kiểm thử | Tiền điều kiện | Các bước thực hiện | Kết quả mong đợi | Mức độ ưu tiên / Nghiêm trọng | Trạng thái |
|---|---|---|---|---|---|---|:---:|
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại | 1. Vào `/register`<br>2. Nhập email hợp lệ, mật khẩu `>= 6 ký tự`, xác nhận mật khẩu khớp<br>3. Bấm "Create Account" | Tạo tài khoản thành công, trả về JWT tokens, điều hướng thẳng vào `/` (Dashboard) | High / Blocker | **PASS** |
| **TC-02** | Auth | Đăng ký thất bại khi email đã tồn tại | Email đã đăng ký | 1. Vào `/register`<br>2. Nhập email đã có trong hệ thống<br>3. Bấm "Create Account" | Báo lỗi `400 Bad Request` với message "Email already registered", không tạo trùng | High / Major | **PASS** |
| **TC-03** | Auth | Đăng ký thất bại khi xác nhận mật khẩu không khớp | Trang `/register` | 1. Nhập password và confirmPassword khác nhau<br>2. Bấm "Create Account" | Báo lỗi validation "Passwords do not match", form không gửi request lên server | Medium / Normal | **PASS** |
| **TC-04** | Auth | Đăng nhập thành công với mật khẩu đúng | User đã đăng ký | 1. Vào `/login`<br>2. Nhập email và password đúng<br>3. Bấm "Sign In" | Đăng nhập thành công (HTTP 200), lưu token, chuyển hướng vào `/` hiển thị email user | High / Blocker | **PASS** |
| **TC-05** | Auth | Đăng nhập thất bại với email không tồn tại (Chống User Enumeration) | Email chưa đăng ký | 1. Vào `/login`<br>2. Nhập email chưa từng đăng ký và mật khẩu bất kỳ<br>3. Bấm "Sign In" | Trả về `401 Unauthorized` với message "Incorrect email or password", hiển thị toast lỗi mà không reload trang | High / Security | **PASS** |
| **TC-06** | Auth | Đăng nhập thất bại với mật khẩu sai (Chống User Enumeration) | Email đã đăng ký | 1. Vào `/login`<br>2. Nhập email đúng nhưng mật khẩu sai<br>3. Bấm "Sign In" | Trả về `401 Unauthorized` với message "Incorrect email or password" (giống hệt TC-05) | High / Security | **PASS** |
| **TC-07** | Auth | Axios 401 không bị reload loop khi đăng nhập sai | Đang ở `/login` | 1. Nhập sai thông tin đăng nhập<br>2. Bấm "Sign In" | Màn hình không bị giật/reload trang liên tục; thông báo lỗi hiển thị rõ ràng cho user | High / Major | **PASS** |
| **TC-08** | Auth | Đăng xuất xóa sạch Token và Cache bộ nhớ | Đã đăng nhập | 1. Bấm nút "Logout" trên Header<br>2. Quan sát LocalStorage và React Query Cache | Xóa access/refresh token khỏi storage, xóa query cache, chuyển hướng về `/login` | High / Major | **PASS** |
| **TC-09** | Security | Token hết hạn bị từ chối truy cập | Có access token đã hết hạn | 1. Gửi request kèm token hết hạn tới `GET /api/v1/auth/me` | Trả về `401 Unauthorized` ("Invalid authentication token"), không cho phép truy cập | High / Critical | **PASS** |
| **TC-10** | Security | Token bị sửa chữ ký (tampered) bị từ chối | Có token bị sửa đổi | 1. Thay đổi vài ký tự chữ ký của JWT<br>2. Gửi request kèm token đó | Trả về `401 Unauthorized`, chặn đứng request | High / Critical | **PASS** |
| **TC-11** | Security | Refresh token không được dùng làm Access token | Có refresh token | 1. Đính kèm refresh token vào `Authorization: Bearer <refresh_token>`<br>2. Gọi `GET /api/v1/todos` | Trả về `401 Unauthorized` do sai token type (yêu cầu access token) | High / Security | **PASS** |
| **TC-12** | Todo Security | User A không thể đọc Todo của User B (BOLA/IDOR) | User A & B đều có tài khoản | 1. User B tạo todo có ID X<br>2. User A gọi `GET /api/v1/todos/X` | Trả về `404 Not Found`, User A không xem được nội dung todo của B | High / Critical | **PASS** |
| **TC-13** | Todo Security | User A không thể cập nhật Todo của User B | User A & B đều có tài khoản | 1. User B có todo ID X<br>2. User A gửi `PUT /api/v1/todos/X` với payload sửa title | Trả về `404 Not Found`, dữ liệu todo của B không bị thay đổi | High / Critical | **PASS** |
| **TC-14** | Todo Security | User A không thể xóa Todo của User B | User A & B đều có tài khoản | 1. User B có todo ID X<br>2. User A gửi `DELETE /api/v1/todos/X` | Trả về `404 Not Found`, todo của B vẫn nguyên vẹn | High / Critical | **PASS** |
| **TC-15** | Todo CRUD | Tạo mới Todo với Title và Description hợp lệ | Đã đăng nhập | 1. Bấm "Add Todo"<br>2. Nhập Title & Description<br>3. Bấm "Create" | Todo mới xuất hiện ngay trên danh sách với completed = false | High / Normal | **PASS** |
| **TC-16** | Todo CRUD | Tạo Todo thất bại khi bỏ trống Title | Đã đăng nhập | 1. Bấm "Add Todo"<br>2. Bỏ trống Title<br>3. Bấm "Create" | Form báo lỗi validation "Title is required", không gửi request lên backend | Medium / Normal | **PASS** |
| **TC-17** | Todo Logic | Đổi trạng thái Todo từ hoàn thành sang chưa hoàn thành (Boolean Toggle) | Todo đang completed = True | 1. Bấm bỏ chọn checkbox của Todo<br>2. F5 tải lại trang | Checkbox hiển thị chưa hoàn thành, gọi API/DB xác nhận `completed = False` | High / Critical | **PASS** |
| **TC-18** | Todo Logic | Cập nhật một phần (Partial update): sửa title giữ nguyên description | Todo có sẵn description | 1. Gửi `PUT /api/v1/todos/{id}` chỉ gồm `{"title": "New Title"}`<br>2. Kiểm tra lại todo | Title đổi mới, `description` cũ vẫn được giữ nguyên vẹn | High / Major | **PASS** |
| **TC-19** | Todo Logic | Form Todo reset giá trị khi chuyển đổi Todo đang sửa | Đang ở Todo page | 1. Bấm Edit Todo 1 (xem dữ liệu)<br>2. Đóng và bấm Edit Todo 2 | Form nạp đúng dữ liệu của Todo 2, không giữ lại giá trị cũ của Todo 1 | Medium / Normal | **PASS** |
| **TC-20** | Todo Logic | Thứ tự hiển thị Todo luôn cố định (Deterministic ordering) | User có nhiều Todo | 1. Tạo nhiều Todo<br>2. Toggle trạng thái hoặc sửa nội dung Todo bất kỳ<br>3. Tải lại trang | Danh sách luôn sắp xếp theo `created_at DESC, id DESC`, Todo không bị nhảy vị trí lung tung | High / Major | **PASS** |
| **TC-21** | Todo State | Rollback giao diện khi cập nhật Todo thất bại (Optimistic Update) | Đang ở Todo page | 1. Giả lập ngắt mạng hoặc backend trả về 500 khi update todo<br>2. Bấm toggle todo | Giao diện tự động hoàn tác (rollback) trạng thái checkbox về ban đầu, kèm toast báo lỗi | Medium / Major | **PASS** |
| **TC-22** | Cache | Cách ly Redis Cache giữa các User | User A & B đều có dữ liệu | 1. User A gọi `GET /todos`<br>2. User B gọi `GET /todos` | Cache key được phân theo user ID, User B không nhận nhầm danh sách của User A | High / Critical | **PASS** |
| **TC-23** | Cache | Invalidate Cache ngay khi có thay đổi (Create/Update/Delete) | Đã có cache danh sách | 1. Gọi `GET /todos` (dữ liệu được cache)<br>2. Tạo mới hoặc xóa 1 todo<br>3. Gọi lại `GET /todos` | Trả về danh sách mới nhất ngay lập tức, không phục vụ cache cũ 5 phút | High / Major | **PASS** |
| **TC-24** | Performance | Lấy danh sách Todo không phát sinh N+1 Query | User có nhiều Todo | 1. Theo dõi query log database khi gọi `GET /todos` | Chỉ thực thi 1 câu query select todo và 1 câu count, không lặp query select user theo từng todo | Medium / Performance | **PASS** |

---

## 4. Defect Tracking & Known Limitations
- **Tình trạng khắc phục**: Toàn bộ 14 lỗi ghi nhận ban đầu trong `docs/BUG_REPORT.md` đã được xử lý triệt để và kiểm chứng đạt 100% qua 24 Test Cases trên.
- **Giới hạn đã biết (Known Limitations)**:
  - Chưa hỗ trợ tính năng quên mật khẩu / gửi email kích hoạt (hệ thống hiện cấp token trực tiếp khi đăng ký).
  - Chưa triển khai phân quyền nhóm hoặc chia sẻ todo giữa nhiều người dùng (đây là phạm vi của Task 3A: Technical Spec).
