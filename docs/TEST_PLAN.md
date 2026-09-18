# Manual Test Plan: Fabbi Todo App — Auth, Authorization & Regression Suite

## 1. Scope & Objective

- **Mục tiêu kiểm thử**: Xác thực các fix của Tier 1 (JWT expiry, IDOR, cache
  isolation/invalidation, boolean toggle, partial update, frontend logout) và
  phát hiện hồi quy (regression) trước khi merge `feature/tier1-fixes` vào
  `main`.
- **Phạm vi kiểm thử**: Authentication, Authorization (IDOR / data isolation),
  Todo CRUD business logic, Redis caching, Frontend state management (session
  cleanup).
- **Ngoài phạm vi**: Load/performance testing, Task 3A (Todo Sharing — chưa
  implement), penetration testing toàn diện (chỉ cover các lỗ hổng đã biết).

## 2. Test Environment & Prerequisites

- Base URL Backend: `http://localhost:8000`
- Base URL Frontend: `http://localhost:5173` (dev) hoặc `http://localhost:3000`
  (docker compose)
- Stack: `docker compose up -d` (Postgres 16, Redis 7, backend, frontend)
- Pre-seeded Test Accounts (tạo mới qua `/register` nếu DB chưa có):
  - Account 1 (User A): `user_a@test.com` / `Password@123`
  - Account 2 (User B): `user_b@test.com` / `Password@123`
- Tool hỗ trợ: trình duyệt (2 cửa sổ ẩn danh riêng biệt cho A và B), hoặc
  Postman/curl để gọi API trực tiếp và kiểm tra response code/body.
- Backend tự động pytest tương ứng: `backend/tests/test_tier2_scenarios.py`
  (tham khảo chéo — các TC dưới đây là bản manual/E2E song song với bộ tự
  động, không thay thế nhau).

## 3. Test Cases Matrix

| TC ID | Module / Feature | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|---|---|---|---|---|---|---|---|
| TC-01 | Auth | Login thành công với mật khẩu đúng | User đã đăng ký | 1. Nhập email/pass đúng<br>2. Bấm Login | Trả về token, chuyển hướng vào Todo page, header hiển thị đúng email | High / Blocker | |
| TC-02 | Auth | Login thất bại với mật khẩu sai | User đã đăng ký | 1. Nhập email đúng, pass sai<br>2. Bấm Login | Báo lỗi (toast), **không** set token vào localStorage, ở lại trang login | Medium / Security | |
| TC-03 | Auth | Đăng ký trùng email bị từ chối | Email đã tồn tại | 1. Register lại với email đã có | HTTP 400, thông báo "Email already registered", không tạo user mới | Medium / Major | |
| TC-04 | Auth | Access token hết hạn bị từ chối (regression guard cho bug JWT `verify_exp=False`) | User đã login, có access token | 1. Đợi token hết hạn (hoặc set `ACCESS_TOKEN_EXPIRE_MINUTES=0` tạm thời để test nhanh)<br>2. Gọi `GET /api/v1/todos` với token đã hết hạn | HTTP 401 `Invalid authentication token`, **không** trả về data | **Critical / Blocker** | |
| TC-05 | Auth | Token bị tamper (đổi chữ ký/payload thủ công) bị từ chối | — | 1. Lấy 1 token hợp lệ, sửa 1 ký tự trong phần payload/signature<br>2. Gọi API với token đã sửa | HTTP 401, không xác thực được | Critical / Blocker | |
| TC-06 | Auth | Gọi API không có token | — | 1. Gọi `GET /api/v1/todos` không kèm header `Authorization` | HTTP 401/403 | High / Major | |
| TC-07 | State Mgmt | Logout xoá sạch session (regression guard cho bug logout không clear cache khi `onSuccess`) | User đã login, đã có vài todo hiển thị | 1. Bấm Logout<br>2. Kiểm tra DevTools → Application → Local Storage<br>3. Truy cập lại `/` bằng URL trực tiếp | `access_token`/`refresh_token` bị xoá khỏi localStorage; bị redirect về `/login`; **không** còn thấy todo cũ nào thoáng qua trước khi redirect | High / Major | |
| TC-08 | State Mgmt | Đăng nhập user khác trên cùng trình duyệt sau khi logout | Vừa logout User A ở TC-07 | 1. Login bằng User B trên cùng tab/trình duyệt vừa logout A | Dashboard chỉ hiển thị todo của User B, **không** có todo còn sót của User A (kiểm tra cache React Query đã bị clear) | High / Security | |
| TC-09 | Todo Security (IDOR) | User A không thể **xem** Todo của User B | User A & B đã login, User B có 1 todo (ghi lại ID) | 1. User A gọi `GET /todos/{id_của_B}` (hoặc sửa URL trên UI nếu có deep link) | HTTP 404 Not Found (không lộ thông tin todo) | **Critical / Blocker** | |
| TC-10 | Todo Security (IDOR) | User A không thể **sửa** Todo của User B | Như trên | 1. User A gọi `PUT /todos/{id_của_B}` với body bất kỳ | HTTP 404; verify lại bằng User B: todo **không** bị thay đổi | **Critical / Blocker** | |
| TC-11 | Todo Security (IDOR) | User A không thể **xoá** Todo của User B | Như trên | 1. User A gọi `DELETE /todos/{id_của_B}` | HTTP 404; verify lại bằng User B: todo vẫn còn tồn tại | **Critical / Blocker** | |
| TC-12 | Todo Security (IDOR) | Danh sách todo của User A không lẫn todo của User B | User A & B đều có todo riêng | 1. User A gọi `GET /todos`<br>2. Kiểm tra toàn bộ `items[]` | Chỉ chứa todo thuộc `user_id` của User A | Critical / Blocker | |
| TC-13 | Todo Logic | Đổi trạng thái todo từ hoàn thành → chưa hoàn thành (regression guard cho bug `if todo_data.completed:` falsy) | Todo đang `completed = true` | 1. Bấm checkbox bỏ completed (hoặc `PUT` với `{"completed": false}`)<br>2. Refresh trang / gọi lại `GET /todos/{id}` | Todo vẫn ở trạng thái `completed = false` sau khi refresh (không bị bỏ qua do falsy-check) | High / Major | |
| TC-14 | Todo Logic | Partial update không xoá mất `description` (regression guard cho bug `model_dump()` thiếu `exclude_unset=True`) | Todo có sẵn `description` khác rỗng | 1. Gọi `PUT /todos/{id}` chỉ với `{"title": "New title"}` (không gửi `description`) | `title` cập nhật thành công; `description` **giữ nguyên** giá trị cũ, không bị null | **Critical / Major** | |
| TC-15 | Todo Logic | Tạo todo với title rỗng bị từ chối | — | 1. Gọi `POST /todos` với `title: ""` | HTTP 422 validation error (theo `Field(min_length=1)`) | Low / Minor | |
| TC-16 | Cache | Tạo todo mới → cache list được invalidate ngay | User đã có sẵn danh sách todo được cache (gọi `GET /todos` ít nhất 1 lần trước đó) | 1. `GET /todos` (primes cache)<br>2. `POST /todos` tạo todo mới<br>3. `GET /todos` lại ngay | Todo mới xuất hiện ngay trong response thứ 2, `total` tăng lên — **không** trả về data cache cũ | High / Major | |
| TC-17 | Cache | Sửa title Todo → cache invalidate ngay (không cần đợi TTL 5 phút) | Todo đã được cache | 1. `GET /todos` (primes cache)<br>2. Sửa title Todo<br>3. `GET /todos` lại ngay | Hiển thị title mới, không nhận cache cũ | High / Major | |
| TC-18 | Cache | Xoá Todo → cache invalidate ngay | Todo đã được cache | 1. `GET /todos` (primes cache)<br>2. `DELETE /todos/{id}`<br>3. `GET /todos` lại ngay | Todo đã xoá **không** còn xuất hiện, `total` giảm | High / Major | |
| TC-19 | Cache Security | Cache list không dùng chung key giữa các user (regression guard cho bug `cache_key = "todos:list"` global) | User A & B đều login | 1. User A gọi `GET /todos` trước (primes cache riêng của A)<br>2. User B gọi `GET /todos` ngay sau | User B nhận đúng danh sách của **mình** (rỗng hoặc todo của B), không nhận nhầm cache list của User A | **Critical / Blocker** | |
| TC-20 | Infra / Config | Secret không bị lộ qua repo | — | 1. Kiểm tra `git ls-files` không còn liệt kê `.env`<br>2. Kiểm tra `.gitignore` có dòng `.env` không bị comment | `.env` không được track; JWT_SECRET/DB password thật đã được rotate (ngoài phạm vi code, xác nhận qua team) | Medium / Security | |

## 4. Defect Tracking & Known Limitations

- **Đã fix và có test tự động đi kèm** (`backend/tests/test_tier2_scenarios.py`
  + `frontend/e2e/*.spec.ts`): TC-04, TC-09 → TC-14, TC-16 → TC-19, TC-07.
- **Chưa cover trong lần test này** (ghi nhận để làm follow-up, không chặn
  merge Tier 1/2):
  - CORS: `backend/app/main.py` cấu hình `allow_origins=["*"]` cùng
    `allow_credentials=True` — kết hợp không hợp lệ theo spec trình duyệt.
    Rủi ro thấp ở thời điểm hiện tại (API dùng Bearer token, không dùng
    cookie), nhưng nên siết origin cụ thể trước khi có tính năng dùng cookie.
  - `requirements.txt` pin `bcrypt==4.3.0` + `passlib==1.7.4` — hai bản này
    **không tương thích** (`passlib` 1.7.4 không hỗ trợ `bcrypt` ≥4.1), khiến
    mọi request `/register` và `/login` crash ngay trên môi trường cài đặt
    sạch theo đúng `requirements.txt`. Đã note riêng cho Task 3B
    (Docker/Infra) — cần pin `bcrypt==4.0.1` hoặc nâng cấp `passlib`.
  - Refresh token không có cơ chế revoke/blacklist khi logout (stateless
    JWT) — nếu access token bị lộ, chỉ hết hiệu lực sau khi token tự
    expire, không có cách vô hiệu hoá sớm.
  - `get_current_user` không kiểm tra `payload["type"] == "access"`, nên
    một refresh token (vốn chỉ nên dùng ở `/auth/refresh`) vẫn dùng được
    để gọi các endpoint thường — nên siết lại loại token được chấp nhận.
