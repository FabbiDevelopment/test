# Manual Test Plan: Full-Stack Todo Application & Regression Verification

> Tài liệu Kế hoạch Kiểm thử Thủ công (Manual Test Plan) phục vụ thẩm định chất lượng các tính năng cốt lõi và kiểm thử hồi quy (regression testing) các lỗi bảo mật & logic đã được khắc phục.

---

## 1. Scope & Objective (Mục tiêu & Phạm vi)

- **Mục tiêu kiểm thử**:
  - Đảm bảo các luồng nghiệp vụ chính hoạt động chính xác từ Frontend đến Backend và Database/Cache.
  - Kiểm tra hồi quy (Regression Testing) nhằm xác thực các lỗi bảo mật và logic quan trọng (JWT expiration, IDOR/BOLA, Cache cross-user leak, Boolean toggle, React state) đã được khắc phục triệt để.
  - Ngăn ngừa các lỗi phát sinh trong tương lai thông qua tài liệu hóa các ca kiểm thử tiêu chuẩn.
- **Phạm vi kiểm thử**:
  - **Module Authentication**: Đăng ký, Đăng nhập, Hạn sử dụng JWT token, Đăng xuất và dọn dẹp phiên.
  - **Module Todo Management**: Tạo, Đọc, Cập nhật một phần, Đổi trạng thái hoàn thành, Xóa Todo.
  - **Module Authorization & Data Isolation**: Kiểm tra ranh giới dữ liệu giữa các người dùng (User A vs User B).
  - **Module Caching**: Cách ly cache Redis theo từng người dùng và cơ chế xóa cache (Invalidation) tức thì khi có biến động dữ liệu.

---

## 2. Test Environment & Prerequisites (Môi trường & Tiền điều kiện)

- **Môi trường Backend**: `http://localhost:8000` (FastAPI, Python 3.11+, SQLAlchemy, PostgreSQL, Redis)
- **Môi trường Frontend**: `http://localhost:3000` (React 19, TypeScript, TanStack Query, Vite)
- **Tài khoản kiểm thử định sẵn**:
  - **Account A (User A)**: `user_a@test.com` / `Password@123`
  - **Account B (User B)**: `user_b@test.com` / `Password@123`
  - **Demo Account**: `demo@test.com` / `Demo@123`
- **Công cụ bổ trợ**: Google Chrome / Firefox (DevTools), Postman / cURL, Redis CLI.

---

## 3. Test Cases Matrix (Bảng Ma trận Ca kiểm thử)

| TC ID | Module | Kịch bản kiểm thử (Scenario) | Tiền điều kiện | Các bước thực hiện (Test Steps) | Kết quả mong đợi (Expected Result) | Mức độ / Độ ưu tiên | Trạng thái |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Chưa có tài khoản | 1. Mở `/register`<br>2. Nhập email hợp lệ và mật khẩu >= 6 ký tự<br>3. Bấm "Create Account" | Tạo tài khoản thành công, trả về JWT token, tự động chuyển hướng vào trang chủ `/` | High / Blocker | **PASS** |
| **TC-02** | Auth | Đăng ký thất bại khi email đã tồn tại | Email đã được đăng ký | 1. Mở `/register`<br>2. Nhập email đã tồn tại<br>3. Bấm "Create Account" | Trả về lỗi `400 Bad Request` ("Email already registered"), hiển thị thông báo lỗi trên UI | High / Major | **PASS** |
| **TC-03** | Auth | Đăng nhập thành công với thông tin đúng | User đã đăng ký | 1. Mở `/login`<br>2. Nhập đúng email và password<br>3. Bấm "Sign In" | Đăng nhập thành công, lưu token vào `localStorage`, điều hướng vào Dashboard | High / Blocker | **PASS** |
| **TC-04** | Auth | Đăng nhập thất bại (Tránh User Enumeration) | Hệ thống có tài khoản A | 1. Nhập email tồn tại nhưng pass sai HOẶC email không tồn tại<br>2. Bấm "Sign In" | API trả về lỗi `401 Unauthorized` chung ("Invalid credentials" hoặc "Incorrect password"), không cho phép dò quét danh sách email | Medium / Security | **PASS** |
| **TC-05** | Auth / Security | Từ chối truy cập khi JWT token đã hết hạn | Token đã hết hạn (`exp` quá hạn) | 1. Gửi request kèm Bearer token đã hết hạn vào `/api/v1/auth/me` | API từ chối với `401 Unauthorized` ("Invalid authentication token"), không cho phép truy cập tài nguyên | Critical / Blocker | **PASS** |
| **TC-06** | Auth | Đăng xuất dọn dẹp sạch token và React Query cache | User đang đăng nhập | 1. Bấm nút "Logout" trên Header<br>2. Kiểm tra `localStorage` và query cache | Token bị xóa khỏi `localStorage`, cache `queryClient.clear()` kích hoạt, điều hướng về `/login` | High / Major | **PASS** |
| **TC-07** | Todo CRUD | Tạo Todo mới thành công | User đã đăng nhập | 1. Bấm "Add Todo"<br>2. Điền Title và Description<br>3. Bấm "Create" | Todo mới xuất hiện ngay lập tức trên UI với checkbox chưa hoàn thành (`completed: false`) | High / Major | **PASS** |
| **TC-08** | Todo Logic | Chuyển trạng thái Todo từ True về False (Boolean toggle) | Todo đang ở trạng thái completed | 1. Bấm bỏ chọn checkbox hoàn thành<br>2. Refresh lại trang (F5) | Todo vẫn duy trì trạng thái chưa hoàn thành (`completed: false`), không bị lỗi giữ nguyên trạng thái True | High / Critical | **PASS** |
| **TC-09** | Todo Logic | Cập nhật một phần (Partial update) không mất description | Todo có sẵn title và description | 1. Bấm nút Edit Todo<br>2. Chỉ thay đổi `title`, giữ nguyên `description`<br>3. Bấm "Save" | `title` được cập nhật mới, `description` cũ vẫn được giữ nguyên vẹn | High / Major | **PASS** |
| **TC-10** | Security / IDOR | User A không thể đọc Todo của User B | User A & B đã đăng nhập, User B có Todo ID `X` | 1. User A gửi request `GET /api/v1/todos/X` | API trả về `403 Forbidden` ("Not authorized to access this todo"), User A không xem được nội dung | Critical / Blocker | **PASS** |
| **TC-11** | Security / IDOR | User A không thể sửa Todo của User B | User A & B đã đăng nhập, User B có Todo ID `X` | 1. User A gửi request `PUT /api/v1/todos/X` sửa title | API trả về `403 Forbidden`, nội dung Todo của User B trong Database không đổi | Critical / Blocker | **PASS** |
| **TC-12** | Security / IDOR | User A không thể xoá Todo của User B | User A & B đã đăng nhập, User B có Todo ID `X` | 1. User A gửi request `DELETE /api/v1/todos/X` | API trả về `403 Forbidden`, Todo của User B không bị xóa khỏi hệ thống | Critical / Blocker | **PASS** |
| **TC-13** | Cache / Isolation | Cách ly cache danh sách Todo giữa các User | User A đã có danh sách Todo được cache | 1. User A gọi `GET /todos` (dữ liệu được nạp vào Redis)<br>2. User B gọi `GET /todos` | User B chỉ thấy Todo của User B, tuyệt đối không nhận Todo của User A từ cache | Critical / Blocker | **PASS** |
| **TC-14** | Cache | Invalidate cache ngay lập tức khi thêm/sửa/xoá Todo | Danh sách Todo đã được cache | 1. Tạo mới hoặc sửa Todo<br>2. Gọi lại `GET /todos` | Trả về dữ liệu mới nhất, cache cũ tương ứng bị xóa lập tức | High / Major | **PASS** |
| **TC-15** | UI / React | Render danh sách Todo ổn định khi thao tác xóa/sửa | Danh sách có >= 3 Todo | 1. Xóa một item ở giữa danh sách<br>2. Quan sát các item còn lại | Các item còn lại giữ đúng trạng thái, không bị nhảy checkbox hoặc sai lệch dữ liệu do dùng `key={todo.id}` | Medium / Normal | **PASS** |
| **TC-16** | UI / State | Rollback giao diện khi cập nhật Todo thất bại | Todo đang hiển thị | 1. Tắt mạng hoặc giả lập lỗi server 500<br>2. Bấm toggle hoàn thành Todo | Giao diện hiển thị thông báo lỗi và tự động hoàn tác (rollback) checkbox về trạng thái ban đầu | Medium / Normal | **PASS** |

---

## 4. Defect Tracking & Regression Summary (Tổng hợp Kiểm thử Hồi quy)

Bảng đối chiếu kiểm tra lại các lỗi đã được sửa chữa trong **Tier 1**:

| Bug ID | Tên lỗi đã khắc phục | Cơ chế phòng ngừa hồi quy | Kết quả kiểm tra lại |
| :--- | :--- | :--- | :--- |
| **BUG-01** | Bỏ qua kiểm tra thời gian hết hạn JWT token | Xóa `options={"verify_exp": False}` trong `security.py` | **Đã xác nhận PASS** (TC-05) |
| **BUG-02** | Lỗ hổng IDOR/BOLA trên endpoint Todo | Kiểm tra `todo.user_id != current_user.id` trả về `403` | **Đã xác nhận PASS** (TC-10, TC-11, TC-12) |
| **BUG-03** | Cache key tĩnh `todos:list` rò rỉ dữ liệu chéo | Định danh cache theo `todos:list:{user_id}:page:{page}:size:{size}` | **Đã xác nhận PASS** (TC-13) |
| **BUG-04** | Dữ liệu Todo bị stale cache 5 phút khi mutation | Gọi `invalidate_user_todos_cache()` khi Create/Update/Delete | **Đã xác nhận PASS** (TC-14) |
| **BUG-05** | Không chuyển được `completed` từ `True` về `False` | Sửa `if todo_data.completed is not None:` | **Đã xác nhận PASS** (TC-08) |
| **BUG-09** | Logout không xóa cache bộ nhớ React Query | Bổ sung `queryClient.clear()` khi logout | **Đã xác nhận PASS** (TC-06) |
| **BUG-10** | Dùng mảng `index` làm React key trong `TodoList` | Thay thế bằng `key={todo.id}` | **Đã xác nhận PASS** (TC-15) |
| **BUG-11** | Optimistic update không rollback khi lỗi | Thêm `queryClient.setQueryData()` trong `onError` | **Đã xác nhận PASS** (TC-16) |

---

## 5. Known Limitations & Recommendations (Hạn chế & Kiến nghị)

1. **Rate Limiting trên Endpoint Authentication**:
   - Hiện tại `/api/v1/auth/login` chưa áp dụng rate limiting (giới hạn số lần thử đăng nhập sai). Cần bổ sung Redis-based rate limiter (ví dụ tối đa 5 lần thử/phút) để ngăn chặn tấn công Brute-force.
2. **Refresh Token Invalidation / Revocation**:
   - Cần bổ sung blacklist vào Redis khi người dùng gọi `/api/v1/auth/logout` để vô hiệu hóa Refresh Token ngay lập tức trước khi nó tự hết hạn sau 7 ngày.
