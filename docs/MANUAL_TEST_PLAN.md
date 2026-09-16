# Manual Test Plan: Authentication, Authorization, Todo Management & Caching

## 1. Scope & Objective

- **Mục tiêu kiểm thử:**
  - Xác thực toàn diện các tính năng cốt lõi của ứng dụng Todo.
  - Kiểm thử hồi quy (Regression Testing) toàn bộ các lỗi bảo mật và nghiệp vụ đã phát hiện & khắc phục ở Tier 1 (User Enumeration, Token Expiration, IDOR, Boolean Toggle, Cache Isolation).
  - Đảm bảo tính toàn vẹn dữ liệu giữa Frontend React SPA, Backend FastAPI, PostgreSQL và Redis Cache.
- **Phạm vi kiểm thử:**
  - **Module Authentication:** Đăng ký, Đăng nhập, Quản lý phiên (JWT Access/Refresh Token), Đăng xuất.
  - **Module Authorization (IDOR):** Kiểm soát truy cập giữa các tài khoản người dùng độc lập.
  - **Module Todo CRUD & Logic:** Tạo, Đọc, Cập nhật từng phần (Partial Update), Đổi trạng thái hoàn thành (Boolean Toggle), Xóa.
  - **Module Caching:** Cache hit, Cache key scoping theo `user_id`, Cache invalidation tức thì khi phát sinh đột biến (Create / Update / Delete).

---

## 2. Test Environment & Prerequisites

- **Base URL Backend:** `http://localhost:8000` (API Docs: `http://localhost:8000/docs`)
- **Base URL Frontend:** `http://localhost:3000`
- **Database:** PostgreSQL 16 (`localhost:5432`)
- **Cache Engine:** Redis 7 (`localhost:6379`)
- **Pre-seeded Test Accounts:**
  - **Account A (User A):** `user_a@test.com` / `Password@123`
  - **Account B (User B):** `user_b@test.com` / `Password@123`
  - **Tools:** Postman / cURL / Swagger UI / Web Browser (Chrome, Firefox, Edge)

---

## 3. Test Cases Matrix

| TC ID | Module | Scenario | Preconditions | Test Steps | Expected Result | Severity / Priority | Status |
|:---|:---|:---|:---|:---|:---|:---|:---:|
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại | 1. Vào `/register`<br>2. Nhập email hợp lệ & password $\ge 8$ ký tự<br>3. Bấm "Create Account" | HTTP 201; Lưu user vào DB; Trả về `access_token` & `refresh_token`; Tự động chuyển hướng vào Dashboard | High / Blocker | PASS |
| **TC-02** | Auth | Đăng ký thất bại khi email đã tồn tại | Email đã đăng ký | 1. Vào `/register`<br>2. Nhập email đã tồn tại<br>3. Bấm "Create Account" | HTTP 400; Thông báo lỗi rõ ràng "Email already registered"; Không tạo bản ghi trùng | Medium / Major | PASS |
| **TC-03** | Auth | Đăng nhập thành công với thông tin đúng | User đã đăng ký | 1. Vào `/login`<br>2. Nhập đúng email & password<br>3. Bấm "Sign In" | HTTP 200; Trả về JWT tokens; Lưu token vào localStorage; Chuyển hướng vào trang chính | High / Blocker | PASS |
| **TC-04** | Auth (Security) | Đăng nhập sai mật khẩu — Phòng chống User Enumeration | User đã tồn tại | 1. Nhập email đúng, mật khẩu sai<br>2. Bấm "Sign In" | HTTP 401; Thông báo lỗi chung: "Invalid email or password"; Không tiết lộ sự tồn tại của email | High / Critical | PASS |
| **TC-05** | Auth (Security) | Đăng nhập với email không tồn tại — Phòng chống User Enumeration | Email không có trong hệ thống | 1. Nhập email ngẫu nhiên, password bất kỳ<br>2. Bấm "Sign In" | HTTP 401; Thông báo lỗi chung giống hệt TC-04: "Invalid email or password" | High / Critical | PASS |
| **TC-06** | Auth (Security) | Từ chối truy cập khi Access Token hết hạn | Token đã hết hạn (`exp` quá hạn) | 1. Sử dụng JWT đã hết hạn gửi request GET `/api/v1/auth/me` | HTTP 401 Unauthorized; Detail: "Invalid authentication token" | High / Critical | PASS |
| **TC-07** | Auth (Security) | Từ chối truy cập khi Token bị giả mạo / sai chữ ký | Token bị thay đổi chữ ký | 1. Thay đổi payload hoặc signature của JWT<br>2. Gửi request GET `/api/v1/todos` | HTTP 401 Unauthorized; Hệ thống từ chối xác thực | High / Critical | PASS |
| **TC-08** | Auth (Security) | Dùng Refresh Token để gọi API yêu cầu Access Token | Có Refresh Token hợp lệ | 1. Đặt Refresh Token vào header `Authorization: Bearer <refresh_token>`<br>2. Gọi GET `/api/v1/auth/me` | HTTP 401 Unauthorized; Detail: "Invalid token type" (chỉ chấp nhận `type: access`) | Medium / Major | PASS |
| **TC-09** | Auth | Đăng xuất người dùng & xóa sạch cache phiên | Đang đăng nhập | 1. Bấm nút "Logout" trên Header<br>2. Kiểm tra `localStorage` và query cache React Query | Token bị gỡ bỏ; Cache React Query bị invalidate/clear hoàn toàn; Redirect về `/login` | Medium / Major | PASS |
| **TC-10** | Auth | Bảo vệ Route Dashboard khi chưa đăng nhập | Chưa đăng nhập / Token rỗng | 1. Truy cập trực tiếp URL `http://localhost:3000/` | Bị chặn và tự động redirect về `http://localhost:3000/login` | Medium / Major | PASS |
| **TC-11** | Authorization (IDOR) | User A không thể đọc chi tiết Todo của User B | User B sở hữu Todo X, User A đã login | 1. User A gửi request GET `/api/v1/todos/{Todo_B_ID}` | HTTP 403 Forbidden; Detail: "Not authorized to access this todo"; User A không xem được dữ liệu | High / Blocker | PASS |
| **TC-12** | Authorization (IDOR) | User A không thể cập nhật Todo của User B | User B sở hữu Todo X, User A đã login | 1. User A gửi PUT `/api/v1/todos/{Todo_B_ID}` sửa title | HTTP 403 Forbidden; Todo của User B trong database giữ nguyên giá trị ban đầu | High / Blocker | PASS |
| **TC-13** | Authorization (IDOR) | User A không thể xóa Todo của User B | User B sở hữu Todo X, User A đã login | 1. User A gửi DELETE `/api/v1/todos/{Todo_B_ID}` | HTTP 403 Forbidden; Bản ghi Todo của User B vẫn an toàn tồn tại trong database | High / Blocker | PASS |
| **TC-14** | Authorization | Cô lập danh sách Todo giữa các người dùng | User A và B đều có các todo riêng | 1. User A gọi GET `/api/v1/todos`<br>2. User B gọi GET `/api/v1/todos` | User A chỉ nhận danh sách todo của User A; User B chỉ nhận danh sách todo của User B; `total` đúng | High / Blocker | PASS |
| **TC-15** | Todo CRUD | Tạo Todo mới thành công | Đã đăng nhập | 1. Bấm "Add Todo"<br>2. Nhập Title: "Work Task", Description: "Details"<br>3. Bấm "Create" | HTTP 201; Todo xuất hiện ngay lập tức trên UI; `completed` mặc định là `false` | High / Major | PASS |
| **TC-16** | Todo CRUD | Lấy danh sách Todo có phân trang | Có $\ge 5$ todos | 1. Gọi GET `/api/v1/todos?page=1&size=2` | HTTP 200; Trả về đúng 2 phần tử `items`; `page: 1, size: 2, total: N` | Medium / Normal | PASS |
| **TC-17** | Todo CRUD | Xóa Todo thành công | Todo đang tồn tại | 1. Bấm icon thùng rác tại dòng Todo<br>2. Xác nhận xóa | HTTP 204 No Content; Item biến mất khỏi giao diện; Database đã xóa bản ghi | High / Major | PASS |
| **TC-18** | Todo Logic | Đổi trạng thái completed từ False sang True | Todo đang `completed: false` | 1. Bấm checkbox của todo | HTTP 200; Text hiển thị gạch ngang (line-through); `completed` thành `true` | High / Critical | PASS |
| **TC-19** | Todo Logic | Đổi trạng thái completed từ True sang False (Regression Fix) | Todo đang `completed: true` | 1. Bấm bỏ chọn checkbox của todo<br>2. Refresh trang (F5) | HTTP 200; Text trở về bình thường; Sau khi reload trạng thái vẫn là `completed: false` | High / Critical | PASS |
| **TC-20** | Todo Logic | Partial Update — Cập nhật Title giữ nguyên Description | Todo có cả title & description | 1. Gọi PUT `/api/v1/todos/{id}` với payload chỉ có `{"title": "New Title"}` (không gửi `description`) | HTTP 200; `title` được đổi thành "New Title"; `description` cũ vẫn được giữ nguyên vẹn | High / Major | PASS |
| **TC-21** | Cache | Cache Hit cho danh sách Todo | User đã gọi GET `/todos` 1 lần | 1. Gọi lại GET `/api/v1/todos`<br>2. Đo thời gian phản hồi | HTTP 200; Phản hồi từ Redis cache (< 10ms); Không query lại PostgreSQL | Medium / Normal | PASS |
| **TC-22** | Cache | Cache Invalidation ngay sau khi tạo Todo mới | Đang có cache của `/todos` | 1. Tạo todo mới qua POST `/api/v1/todos`<br>2. Gọi GET `/api/v1/todos` | Cache cũ bị xóa bởi pattern `todos:user:{user_id}:*`; Danh sách mới hiển thị ngay item vừa tạo | High / Critical | PASS |
| **TC-23** | Cache | Cache Invalidation ngay sau khi sửa / xóa Todo | Đang có cache của `/todos` | 1. Sửa trạng thái hoặc xóa Todo<br>2. Gọi GET `/api/v1/todos` | Cache cũ bị xóa; Danh sách phản ánh ngay sự thay đổi mà không cần chờ TTL hết hạn | High / Critical | PASS |
| **TC-24** | Cache (Security) | Cô lập Cache Key theo User ID | Cả User A và User B cùng truy cập trang 1 | 1. User A load trang `/todos`<br>2. User B load trang `/todos` | Cache key được định danh `todos:user:{user_id}:page:1:size:20`; User B không bao giờ nhận nhầm cache của User A | High / Critical | PASS |

---

## 4. Defect Tracking & Known Limitations

### ✅ Các lỗi đã xác minh khắc phục thành công (Tier 1 & Tier 2 Regressions)
1. **User Enumeration Vulnerability (Auth):** Trước đây backend trả về "User not found" khi email không tồn tại và "Incorrect password" khi sai pass. Đã hợp nhất thành thông báo an toàn: "Invalid email or password" (HTTP 401).
2. **JWT Expiration & Token Type (Security):** Đã bổ sung cấu hình xác thực `verify_exp: True` và kiểm tra tường minh `token_type == "access"`. Refresh token không thể dùng để truy cập API nghiệp vụ.
3. **IDOR Cross-User Access (Authorization):** Bổ sung kiểm tra quyền sở hữu `if todo.user_id != current_user.id:` trả về HTTP 403 Forbidden trên các endpoint GET, PUT, DELETE.
4. **Falsy Boolean State Lost (Todo Logic):** Sửa lỗi điều kiện `if todo_data.completed:` khiến giá trị `False` bị bỏ qua; chuyển sang dùng `model_dump(exclude_unset=True)`.
5. **Shared Global Cache Collision (Cache):** Bổ sung tiền tố định danh `user_id` vào cache key (`todos:user:{user_id}:page:...`) và áp dụng `delete_pattern(f"todos:user:{user_id}:*")` khi có mutation.
6. **Frontend Stale Cache on Logout (UI):** Thêm `queryClient.clear()` khi người dùng bấm logout, ngăn chặn rò rỉ dữ liệu cũ trên browser cache của phiên kế tiếp.

### ⚠️ Ghi chú & Đề xuất nâng cấp trong tương lai (Future Enhancements)
- **Token Blacklisting / Revocation:** Hiện tại khi user logout, token bị xoá ở client nhưng vẫn còn hiệu lực đến khi hết `exp`. Trong Tier 3 / Production, có thể lưu `jti` vào Redis blacklist với TTL bằng thời gian sống còn lại của token.
- **Brute-force Protection:** Cân nhắc tích hợp Rate Limiting (ví dụ: `slowapi` hoặc Redis rate limiter) cho endpoint `/api/v1/auth/login` (tối đa 5 lần thử sai / phút).
