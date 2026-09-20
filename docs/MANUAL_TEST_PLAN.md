# Manual Test Plan: Fabbi Todo App (Tier 2 Quality Assurance)

## 1. Scope & Objective
- **Mục tiêu kiểm thử**: Xác thực chất lượng phần mềm toàn diện, đảm bảo an toàn xác thực (Authentication), phân quyền chuẩn xác (Authorization), logic quản lý Todo CRUD không bị lỗi hồi quy (regression) và cơ chế xóa cache (Redis & Frontend React Query) hoạt động chính xác.
- **Phạm vi kiểm thử**:
  - Authentication & JWT Token Management
  - Authorization & Data Isolation (Chống rò rỉ dữ liệu giữa các User / IDOR)
  - Todo CRUD Operations & State Management
  - Cache Isolation & Invalidation (Redis & React Query Cache)

---

## 2. Test Environment & Prerequisites
- **Backend API**: `http://localhost:8000`
- **Frontend App**: `http://localhost:3000`
- **Database**: PostgreSQL 16
- **Cache**: Redis 7
- **Tài khoản Kiểm thử Tiêu chuẩn**:
  - User A: `user_a@test.com` / `Password@123`
  - User B: `user_b@test.com` / `Password@123`

---

## 3. Test Cases Matrix (Ma trận Kịch bản Kiểm thử)

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| **TC-01** | Auth | Đăng ký tài khoản thành công | Chưa có tài khoản | 1. Vào `/register`<br>2. Nhập email hợp lệ & password<br>3. Bấm Register | Đăng ký thành công, tự động cấp JWT Token và chuyển sang giao diện `/todos` | High / Blocker | Pass |
| **TC-02** | Auth | Đăng ký thất bại khi trùng Email | Email đã tồn tại trong DB | 1. Vào `/register`<br>2. Nhập email đã trùng<br>3. Bấm Register | Hệ thống thông báo lỗi HTTP 400 "Email already registered" | High / Major | Pass |
| **TC-03** | Auth | Đăng nhập thành công | Tài khoản đã đăng ký | 1. Vào `/login`<br>2. Nhập email & password đúng<br>3. Bấm Login | Đăng nhập thành công, nhận token và vào trang `/todos` | High / Blocker | Pass |
| **TC-04** | Auth | Từ chối JWT Token đã hết hạn | Token đã hết hạn `exp` | 1. Đính kèm token hết hạn vào Header `Authorization: Bearer <token>`<br>2. Gọi API `GET /api/v1/todos` | Trả về lỗi HTTP 401 Unauthorized | Critical / Blocker | Pass |
| **TC-05** | Authorization | User A không thể đọc Todo của User B (IDOR) | User A & B đã có tài khoản | 1. User B tạo Todo có ID `X`<br>2. User A gọi `GET /api/v1/todos/X` | Trả về 404 Not Found (không làm lộ dữ liệu của User B) | Critical / Blocker | Pass |
| **TC-06** | Authorization | User A không thể sửa Todo của User B | User A & B đã có tài khoản | 1. User B tạo Todo ID `X`<br>2. User A gọi `PUT /api/v1/todos/X` với payload sửa title | Trả về 404 Not Found, dữ liệu của User B giữ nguyên | Critical / Blocker | Pass |
| **TC-07** | Authorization | User A không thể xóa Todo của User B | User A & B đã có tài khoản | 1. User B tạo Todo ID `X`<br>2. User A gọi `DELETE /api/v1/todos/X` | Trả về 404 Not Found, Todo của User B không bị xóa | Critical / Blocker | Pass |
| **TC-08** | Todo Logic | Đổi trạng thái `completed` từ `true` về `false` | Todo đang ở trạng thái `completed = true` | 1. Bỏ chọn Checkbox trên giao diện hoặc gọi `PUT /todos/X` với `completed: false`<br>2. Tải lại trang | Trạng thái `completed` chuyển về `false` và lưu chính xác trong DB | High / Major | Pass |
| **TC-09** | Todo Logic | Cập nhật một phần (Partial Update) không làm mất Description | Todo đã có `title` và `description` | 1. Gửi request `PUT /todos/X` chỉ với trường `title` mới | `title` được cập nhật mới, `description` cũ giữ nguyên không bị xóa hay `null` | Medium / Major | Pass |
| **TC-10** | Cache | Redis Cache cô lập theo từng User | User A & B đã login | 1. User A gọi `GET /todos` (lưu cache)<br>2. User B gọi `GET /todos` | User B nhận đúng danh sách Todo của User B, không bị nhận trùng cache của User A | Critical / Blocker | Pass |
| **TC-11** | Cache | Làm sạch Redis Cache khi Mutation (Create/Update/Delete) | Dữ liệu Todo đã được lưu cache | 1. Gọi `GET /todos`<br>2. Thực hiện tạo mới/sửa/xóa Todo<br>3. Gọi lại `GET /todos` | Cache rác cũ bị xóa, hệ thống trả về danh sách mới nhất | High / Major | Pass |
| **TC-12** | Frontend | Xóa sạch React Query Cache khi Logout | User A đang đăng nhập trên trình duyệt | 1. User A bấm Logout<br>2. User B đăng nhập trên cùng trình duyệt | Không còn hiển thị dữ liệu Todo của User A trong bộ nhớ tạm React Query | High / Major | Pass |

---

## 4. Defect Tracking & Summary
- Tất cả 12 testcases trọng yếu ở trên đã được thử nghiệm và vượt qua (Pass 100%) sau khi áp dụng các bản sửa lỗi ở Tier 1 và bổ sung các kịch bản kiểm thử tự động ở Tier 2.
- Ứng dụng sẵn sàng cho việc tối ưu hạ tầng Docker và đánh chỉ mục Database ở Tier 3.
