# Kế Hoạch Triển Khai Tier 2: Testing Strategy & Implementation

Nhiệm vụ của Tier 2 là xây dựng chiến lược kiểm thử toàn diện, đảm bảo rằng các tính năng cốt lõi và các bản vá lỗi ở Tier 1 hoạt động chính xác và không bị thoái lui (regression).

## Mục Tiêu Cụ Thể
- **Tier 2A**: Viết bài kiểm thử tự động cho Backend bằng `pytest` (Tối thiểu 3 scenarios).
- **Tier 2B**: Thiết lập và viết bài kiểm thử E2E bằng `Playwright` (Tối thiểu 2 scenarios).
- **Tier 2C**: Lập một bản Kế hoạch kiểm thử thủ công (Manual Test Plan) dựa trên mẫu có sẵn.

## Các Bước Triển Khai

### Bước 1: Hoàn thiện Manual Test Plan (Tier 2C)
- Dựa vào file `templates/TEST_PLAN_TEMPLATE.md`, tôi sẽ tạo ra file `docs/TEST_PLAN.md`.
- File này sẽ định nghĩa chi tiết các kịch bản kiểm thử (Test Scenarios) cho cả tính năng Đăng nhập/Xác thực (Authentication) và Phân quyền (Authorization).
- Vì chúng ta đã fix toàn bộ bug ở Tier 1, trạng thái của các test case này sẽ được đánh dấu là **Pass**.

### Bước 2: Viết Backend Tests với Pytest (Tier 2A)
Tôi sẽ tiến hành viết các bài test trong thư mục `backend/tests/` (ví dụ `test_auth.py`, `test_todos.py`) để bao phủ 3 kịch bản cực kỳ quan trọng:
1. **Kiểm tra JWT**: Hệ thống phải từ chối (HTTP 401) nếu JWT token bị hết hạn.
2. **Kiểm tra Phân quyền (Data Isolation)**: User A không thể gọi API để Đọc/Sửa/Xóa Todo của User B (mong đợi HTTP 403 hoặc 404).
3. **Kiểm tra Logic Toggle**: Cập nhật trạng thái `completed` từ `true` về lại `false` phải thành công.

Sau khi viết xong, chúng ta sẽ chạy lệnh `pytest tests/ -v` ở backend để đảm bảo mọi thứ xanh (Passed).

### Bước 3: Cài đặt và Viết Playwright E2E Tests (Tier 2B)
- Di chuyển vào thư mục `frontend/` (hoặc tạo thư mục `e2e/` mới).
- Khởi tạo Playwright bằng lệnh `npm init playwright@latest`.
- Viết 2 kịch bản E2E kiểm tra toàn bộ ứng dụng từ góc nhìn của trình duyệt:
  1. **Full User Journey**: Đăng ký/Đăng nhập -> Tạo Todo -> Đánh dấu hoàn thành -> Đăng xuất.
  2. **Cross-User Data Isolation**: Đăng nhập User A tạo Todo X, sau đó đăng nhập User B và kiểm tra xem Todo X có bị ẩn đi hoàn toàn hay không.
- Chạy lệnh `npx playwright test` để xác minh trình duyệt chạy ổn định.

---
**Bạn có đồng ý với lộ trình này không? Chúng ta có thể bắt đầu với Bước 1 (Tạo Manual Test Plan) ngay bây giờ nhé?**
