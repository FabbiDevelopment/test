# Kế Hoạch Kiểm Thử Thủ Công (Manual Test Plan)

Tài liệu này định nghĩa ma trận kiểm thử hồi quy (regression) và xác thực toàn diện cho ứng dụng Todo App (Tier 2C), tuân thủ theo biểu mẫu chuẩn [`templates/TEST_PLAN_TEMPLATE.md`](../templates/TEST_PLAN_TEMPLATE.md).

---

## 1. Scope & Objective (Mục Tiêu & Phạm Vi)

- **Mục tiêu kiểm thử**: Xác thực tính chính xác của các luồng nghiệp vụ cốt lõi, đảm bảo an ninh hệ thống (Authentication, Authorization, chống IDOR) và xác nhận 11 lỗi phát hiện trong Tier 1 đã được sửa triệt để, không bị hồi quy (regression).
- **Phạm vi kiểm thử**:
  - Authentication & Token Security (JWT access/refresh token, expiration, logout cleanup).
  - Authorization & Data Boundary (IDOR protection giữa các tài khoản).
  - Todo CRUD Operations & Edge Cases (Boolean toggle, partial update preservation, deterministic ordering).
  - Frontend UI/UX State (Form edit sync, unique React reconciliation keys, TanStack Query cache).
  - Performance & Caching (User-scoped Redis cache, cache invalidation on mutation).

---

## 2. Test Environment & Prerequisites (Môi Trường & Tiền Đề)

- **Base URL Backend**: `http://localhost:8000` (Swagger Docs: `http://localhost:8000/docs`)
- **Base URL Frontend**: `http://localhost:3000`
- **Database**: PostgreSQL 16 (`localhost:5432`)
- **Cache**: Redis 7 (`localhost:6379`)
- **Tài khoản kiểm thử mẫu (Pre-seeded Accounts)**:
  - Account 1 (Demo User): `demo@test.com` / `Demo@123`
  - Account 2 (User A - Tester): `tester_a@test.com` / `Password@123`
  - Account 3 (User B - Attacker/Cross-User): `tester_b@test.com` / `Password@123`

---

## 3. Test Cases Matrix (Ma Trận Kịch Bản Kiểm Thử)

| TC ID | Module | Test Scenario | Preconditions | Test Steps | Expected Result | Actual Result | Severity | Priority | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại trong hệ thống | 1. Vào `/register`<br>2. Nhập email hợp lệ & password $\ge$ 8 ký tự<br>3. Bấm "Create Account" | Tạo tài khoản thành công, nhận JWT tokens, tự động chuyển hướng vào `/` (Dashboard) | Khớp mong đợi: Tài khoản tạo mới thành công, nhận token và redirect vào Dashboard mượt mà | Blocker | P1 (High) | **PASS** |
| **TC-02** | Auth | Đăng nhập thất bại khi sai mật khẩu (Chống User Enumeration) | Tài khoản đã tồn tại | 1. Vào `/login`<br>2. Nhập đúng email, nhập sai mật khẩu<br>3. Bấm "Sign In" | Báo lỗi chung HTTP 401 (`"Invalid email or password"`), không để lộ sự tồn tại của email | Khớp mong đợi: Trả về HTTP 401 với thông báo lỗi bảo mật chung, không rò rỉ email | Security | P2 (Medium) | **PASS** |
| **TC-03** | Auth / Security | Từ chối Access Token đã hết hạn | Token đã quá hạn 30 phút (`exp` < now) | 1. Dùng token cũ gọi API `/api/v1/auth/me` hoặc `/api/v1/todos` | Trả về HTTP 401 Unauthorized (`"Could not validate credentials"`) | Khớp mong đợi: FastAPI từ chối token hết hạn ngay tại middleware dependency | Critical | P1 (High) | **PASS** |
| **TC-04** | Auth / Security | Từ chối dùng Refresh Token để gọi API thông thường | Có Refresh Token hợp lệ | 1. Gửi Header `Authorization: Bearer <refresh_token>` vào `/api/v1/todos` | Trả về HTTP 401 Unauthorized do token type không phải `"access"` | Khớp mong đợi: Chặn đứng truy cập trái phép, trả về HTTP 401 đúng quy chuẩn | Security | P1 (High) | **PASS** |
| **TC-05** | Auth / Frontend | Đăng xuất xóa sạch Cache Frontend | Đang đăng nhập và có Todo trên giao diện | 1. Bấm nút "Logout" trên Header<br>2. Kiểm tra `localStorage`<br>3. Kiểm tra React Query cache | Token bị xóa sạch, query cache bị `clear()`, chuyển hướng về `/login` | Khớp mong đợi: `localStorage` rỗng, cache bộ nhớ bị dọn sạch, không lưu vết session cũ | Major | P1 (High) | **PASS** |
| **TC-06** | Todo Security | Chống IDOR: User B không thể đọc Todo của User A | User A có Todo bí mật (ID: `uuid_a`) | 1. User B đăng nhập<br>2. User B gọi `GET /api/v1/todos/{uuid_a}` | Trả về HTTP 403 Forbidden (`"Not authorized to access this todo"`) | Khớp mong đợi: Hệ thống kiểm tra quyền sở hữu và trả về 403 Forbidden | Critical | P1 (High) | **PASS** |
| **TC-07** | Todo Security | Chống IDOR: User B không thể sửa Todo của User A | User A có Todo bí mật (ID: `uuid_a`) | 1. User B gọi `PUT /api/v1/todos/{uuid_a}` với `{ "title": "Hacked" }` | Trả về HTTP 403 Forbidden, Todo của User A giữ nguyên | Khớp mong đợi: Trả về 403, database không bị sửa đổi bởi User B | Critical | P1 (High) | **PASS** |
| **TC-08** | Todo Security | Chống IDOR: User B không thể xóa Todo của User A | User A có Todo bí mật (ID: `uuid_a`) | 1. User B gọi `DELETE /api/v1/todos/{uuid_a}` | Trả về HTTP 403 Forbidden, Todo của User A không bị xóa | Khớp mong đợi: Trả về 403, Todo vẫn tồn tại nguyên vẹn trong tài khoản User A | Critical | P1 (High) | **PASS** |
| **TC-09** | Todo Logic | Đổi trạng thái hoàn thành về chưa hoàn thành (Boolean Toggle) | Todo đang ở trạng thái `completed = true` | 1. Click checkbox bỏ tick trên UI<br>2. F5 hoặc gọi `GET /todos/{id}` | Trạng thái chuyển thành `completed = false`, mất gạch ngang text | Khớp mong đợi: Checkbox bỏ tick thành công, database lưu đúng `completed: false` | Major | P1 (High) | **PASS** |
| **TC-10** | Todo Logic | Giữ nguyên Description khi Partial Update | Todo có cả `title` và `description` | 1. Gửi request `PUT /todos/{id}` chỉ chứa `{ "title": "New Title" }` | `title` đổi mới, `description` cũ không bị đè thành `null` | Khớp mong đợi: `exclude_unset=True` giữ trọn vẹn mô tả ban đầu của người dùng | Major | P1 (High) | **PASS** |
| **TC-11** | Todo Logic | Thứ tự danh sách cố định, không nhảy loạn xạ khi update | Có $\ge$ 5 Todos trong danh sách | 1. Toggle completed của một Todo ở giữa danh sách<br>2. F5 tải lại trang | Danh sách giữ nguyên thứ tự sắp xếp `created_at DESC, id DESC` | Khớp mong đợi: Vị trí các phần tử ổn định, không bị xáo trộn vị trí ngẫu nhiên | Major | P2 (Medium) | **PASS** |
| **TC-12** | Redis Cache | Cô lập Cache Todo giữa các User | User A và User B có Todo riêng biệt | 1. User A tải danh sách Todo<br>2. User B tải danh sách Todo | User B không nhận cache của User A (cache key theo `user_id`) | Khớp mong đợi: Key phân lập `todos:list:{user_id}:*`, dữ liệu hoàn toàn độc lập | Critical | P1 (High) | **PASS** |
| **TC-13** | Redis Cache | Invalidation xóa Cache ngay khi có thay đổi dữ liệu | Đã có cache danh sách Todo | 1. Thêm mới, sửa hoặc xóa Todo<br>2. Gọi ngay `GET /todos` | Trả về dữ liệu mới tức thì, các cache key cũ bị xóa sạch | Khớp mong đợi: `delete_pattern` kích hoạt ngay khi mutation diễn ra | Major | P2 (Medium) | **PASS** |
| **TC-14** | Frontend UI | Form Edit tự động đồng bộ khi chuyển giữa các Todo | Có $\ge$ 2 Todos khác nhau | 1. Bấm Sửa Todo 1 $\rightarrow$ Đóng modal<br>2. Bấm Sửa Todo 2 | Modal hiển thị đúng dữ liệu của Todo 2, không dính dữ liệu cũ | Khớp mong đợi: `useEffect` reset form value theo prop `todo` mới nhất | Minor | P2 (Medium) | **PASS** |
| **TC-15** | Frontend UI | Sử dụng Stable Key cho danh sách React Item | Có danh sách Todo hiển thị | 1. Xóa một Todo ở giữa danh sách<br>2. Kiểm tra DOM rendering | React reconciliation cập nhật chính xác nhờ `key={todo.id}` | Khớp mong đợi: Giao diện cập nhật mượt mà, không chớp giật hay nhảy nhầm state | Minor | P3 (Low) | **PASS** |

---

## 4. Defect Tracking & Known Limitations (Theo Dõi Lỗi & Giới Hạn)

- **Các lỗi đã khắc phục triệt để**:
  - Toàn bộ 11 lỗi phát hiện ở Tier 1 (7 BE + 4 FE) đã được kiểm thử và xác nhận đạt kết quả **PASS**.
- **Giới hạn đã biết (Known Limitations)**:
  - Giao diện Frontend hiện đang hiển thị toàn bộ danh sách Todo (chưa tích hợp cụm phân trang Previous/Next, tính năng này được mở rộng ở Tier 4).
  - API rate limiting hiện chưa cấu hình ngưỡng nghiêm ngặt cho endpoint `/register` (được khuyến nghị bổ sung ở môi trường Production).
