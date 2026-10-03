# Manual Test Plan & Regression Suite: Fabbi Todo App

> **Assessment Module**: Tier 2C — Quality Assurance & Testing Strategy  
> **Author**: Senior Full-Stack & QA Engineer Candidate  
> **Target Release**: v1.0.0-assessment  
> **Status**: Approved & Executed (100% Pass)

---

## 1. Scope & Objective

### 1.1 Objective
Xác thực độ chính xác nghiệp vụ (business correctness), tính toàn vẹn dữ liệu (data integrity), bảo mật phân quyền (authorization boundary) và cơ chế lưu đệm (Redis caching lifecycle) sau khi khắc phục các lỗi nghiêm trọng trong hệ thống Fabbi Todo.

### 1.2 In-Scope
- **Authentication & Token Lifecycle**: Đăng ký, đăng nhập, JWT expiry enforcement, refresh token, ngăn chặn User Enumeration, thu hồi token khi đăng xuất.
- **Todo Management (CRUD)**: Tạo, xem, cập nhật từng phần (partial update), chuyển đổi trạng thái Boolean (toggle), xoá công việc.
- **Data Isolation & IDOR Security**: Ngăn chặn người dùng trái phép truy cập hoặc chỉnh sửa tài nguyên của người dùng khác (BOLA/IDOR).
- **Redis Caching Strategy**: User-scoped cache keys, vô hiệu hoá cache tức thì (cache invalidation) khi có mutation.

### 1.3 Out-of-Scope
- Load testing vượt ngưỡng 10,000 req/s (được đánh giá riêng ở Task 3C Database Tuning).
- Tích hợp nhà cung cấp OAuth2 bên thứ ba (Google/GitHub SSO).

---

## 2. Test Environment & Prerequisites

- **Frontend Application**: `http://localhost:3000` (React 19 + Vite + Tailwind CSS)
- **Backend API Gateway**: `http://localhost:8000` (FastAPI + SQLAlchemy + asyncpg)
- **Database Engine**: PostgreSQL 16 (Port 5432)
- **Cache Engine**: Redis 7 (Port 6379)
- **Pre-seeded Accounts**:
  - `User A (Primary)`: `user_a@test.com` / `Password@123`
  - `User B (Attacker / Collaborator)`: `user_b@test.com` / `Password@123`
  - `Demo Account`: `demo@test.com` / `Demo@123`

---

## 3. Comprehensive Test Cases Matrix

| TC ID | Module | Scenario / Test Objective | Preconditions | Test Steps | Expected Result | Severity | Test Type | Status |
|---|---|---|---|---|---|---|---|---|
| **TC-01** | Auth | Đăng ký tài khoản mới thành công | Email chưa tồn tại | 1. POST `/api/v1/auth/register`<br>2. Payload: email hợp lệ, password >= 8 ký tự | HTTP 201 Created, trả về `access_token` và `refresh_token`, mã hoá an toàn | High | API / E2E | **PASS** |
| **TC-02** | Auth | Đăng ký thất bại với email đã tồn tại | Email `demo@test.com` đã có | 1. POST `/api/v1/auth/register` với email trùng | HTTP 400 Bad Request: `detail: "Email already registered"` | High | API | **PASS** |
| **TC-03** | Auth | Đăng nhập thành công với thông tin đúng | Account đã active | 1. POST `/api/v1/auth/login` với email & pass đúng | HTTP 200 OK, trả về token cặp hợp lệ | Critical | API / E2E | **PASS** |
| **TC-04** | Auth | Ngăn chặn User Enumeration khi sai mật khẩu hoặc sai email | - | 1. POST `/api/v1/auth/login` với email không tồn tại<br>2. POST login với email đúng nhưng sai pass | Cả 2 trường hợp đều trả về **HTTP 401** chung `detail: "Invalid email or password"` (Không để lộ 404) | High | Security | **PASS** |
| **TC-05** | Auth | Từ chối JWT token đã hết hạn (`verify_exp`) | Token sinh ra với `exp < now` | 1. Gửi request GET `/api/v1/auth/me` kèm header expired token | HTTP 401 Unauthorized: `detail: "Invalid authentication token"` | Critical | Security | **PASS** |
| **TC-06** | Auth | Từ chối Refresh Token dùng sai mục đích | Refresh token hợp lệ | 1. Gửi GET `/api/v1/auth/me` với Bearer Refresh Token | HTTP 401 Unauthorized: `detail: "Invalid token payload"` (chỉ chấp nhận `type: access`) | High | Security | **PASS** |
| **TC-07** | Auth | Đăng xuất dọn sạch Client Cache & Storage | User đang đăng nhập | 1. Click "Logout" trên giao diện | Token bị xoá khỏi `localStorage`, `queryClient.clear()` xoá sạch dữ liệu nhạy cảm trên bộ nhớ trình duyệt | Medium | Frontend / E2E | **PASS** |
| **TC-08** | Todo | Tạo Todo thành công và làm mới Cache | User đã xác thực | 1. POST `/api/v1/todos` với `title`, `description` | HTTP 201 Created, todo xuất hiện trên danh sách, cache Redis cũ bị xoá | High | API / E2E | **PASS** |
| **TC-09** | Todo | Chuyển đổi trạng thái Boolean (`completed` false -> true -> false) | Todo đang `completed: true` | 1. PUT `/api/v1/todos/{id}` với `{"completed": false}` | HTTP 200 OK, `completed` lưu thành công giá trị `false` (sửa lỗi `if todo_data.completed:`) | High | Regression | **PASS** |
| **TC-10** | Todo | Cập nhật một phần (Partial Update) không xoá description | Todo có description sẵn | 1. PUT `/api/v1/todos/{id}` chỉ gửi `{"title": "New Title"}` | HTTP 200 OK, `title` đổi mới, `description` cũ được giữ nguyên vẹn | High | Regression | **PASS** |
| **TC-11** | Security | Ngăn chặn IDOR: User B không thể đọc Todo của User A | Todo ID của User A | 1. User B gửi GET `/api/v1/todos/{user_a_todo_id}` | HTTP 403 Forbidden: `"You do not have permission to access this todo"` | Critical | Security | **PASS** |
| **TC-12** | Security | Ngăn chặn IDOR: User B không thể sửa Todo của User A | Todo ID của User A | 1. User B gửi PUT `/api/v1/todos/{user_a_todo_id}` | HTTP 403 Forbidden: `"You do not have permission to modify this todo"` | Critical | Security | **PASS** |
| **TC-13** | Security | Ngăn chặn IDOR: User B không thể xoá Todo của User A | Todo ID của User A | 1. User B gửi DELETE `/api/v1/todos/{user_a_todo_id}` | HTTP 403 Forbidden: `"You do not have permission to delete this todo"` | Critical | Security | **PASS** |
| **TC-14** | Cache | Cách ly dữ liệu Cache giữa các User (User-Scoped Cache) | User A có 5 todos | 1. User A gọi list todos (cache được ghi)<br>2. User B gọi list todos | User B nhận danh sách riêng của mình, hoàn toàn không thấy dữ liệu của User A | Critical | Cache/Security | **PASS** |
| **TC-15** | Cache | Vô hiệu hoá Cache khi xoá công việc (Lifecycle Invalidation) | Todo đã được cache | 1. DELETE `/api/v1/todos/{id}`<br>2. Gọi ngay GET `/api/v1/todos` | Trả về tổng số lượng giảm 1, không dính stale cache | Medium | Cache | **PASS** |

---

## 4. Defect Tracking & Resolution Summary

| Bug ID | Phân loại | Tệp tin & Vị trí | Mức độ | Nguyên nhân | Biện pháp khắc phục | Trạng thái |
|---|---|---|---|---|---|---|
| **BUG-01** | Security | `backend/app/core/security.py:56` | **CRITICAL** | `verify_exp: False` bỏ qua kiểm tra hạn dùng token JWT | Đổi sang `verify_exp: True` | **Fixed & Verified** |
| **BUG-02** | Security | `backend/app/api/v1/todos.py:37` | **CRITICAL** | Cache key dùng chung `"todos:list"` làm rò rỉ dữ liệu giữa người dùng | User-scoped key `todos:list:{user_id}:{page}:{size}` | **Fixed & Verified** |
| **BUG-03** | Security | `backend/app/api/v1/todos.py:95, 114, 145` | **CRITICAL** | Lỗ hổng IDOR/BOLA, không kiểm tra quyền sở hữu `user_id` | Thêm kiểm tra `todo.user_id != current_user.id -> 403` | **Fixed & Verified** |
| **BUG-04** | Logic | `backend/app/api/v1/todos.py:123` | **HIGH** | `if todo_data.completed:` coi `False` là falsy, không thể uncheck | Dùng `exclude_unset=True` và kiểm tra `is not None` | **Fixed & Verified** |
| **BUG-05** | Logic | `backend/app/api/v1/todos.py:121` | **HIGH** | `model_dump()` ghi đè `None` vào description khi update title | Dùng `todo_data.model_dump(exclude_unset=True)` | **Fixed & Verified** |
| **BUG-06** | Performance| `backend/app/api/v1/todos.py:48` | **HIGH** | N+1 Query: Gọi SELECT User trong vòng lặp lặp qua từng todo | Tận dụng `current_user.email` sẵn có từ auth session | **Fixed & Verified** |
| **BUG-07** | Cache | `backend/app/api/v1/todos.py:77` | **MEDIUM** | Thiếu cache invalidation khi Create/Update/Delete | Thêm `redis.delete_pattern("todos:list:{user_id}:*")` | **Fixed & Verified** |
| **BUG-08** | UI/State | `frontend/.../TodoList.tsx:42` | **MEDIUM** | Dùng `key={index}` gây lỗi DOM reconciliation khi sort/delete | Chuyển sang `key={todo.id}` | **Fixed & Verified** |
| **BUG-09** | UI/State | `frontend/.../useAuth.ts:24` | **MEDIUM** | Không xoá cache React Query khi Logout | Thêm `queryClient.clear()` khi logout thành công | **Fixed & Verified** |

---

## 5. Automation Mapping

- **Pytest Suite**: `backend/tests/test_auth.py`, `backend/tests/test_todos.py` (18 test cases automated, 100% passed).
- **Playwright Suite**: `e2e/tests/user-journey.spec.ts`, `e2e/tests/data-isolation.spec.ts`.
