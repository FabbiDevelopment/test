# Kế Hoạch Triển Khai Tier 3: Advanced Engineering Skills

Tier 3 tập trung vào các kỹ năng kỹ thuật chuyên sâu của một kỹ sư phần mềm (Thiết kế hệ thống, DevOps/Hạ tầng, và Tối ưu hóa Database). Dưới đây là kế hoạch chi tiết từng bước để hoàn thành xuất sắc yêu cầu.

---

## 🚀 Task 3A: Technical Specification Writing (Todo Sharing)

**Mục tiêu:** Thiết kế hệ thống cho tính năng "Chia sẻ danh sách công việc (Todo Sharing)" mà không cần code.

**Các bước thực hiện:**
1. **Khởi tạo tài liệu:** Đọc nội dung file `templates/SPEC_TEMPLATE.md` để hiểu cấu trúc yêu cầu.
2. **Viết file `docs/TODO_SHARING_SPEC.md`** bao gồm các phần chính:
   - **User Stories & Acceptance Criteria:** Mô tả chi tiết kịch bản người dùng (ai có thể share, share quyền Read/Edit, cách thu hồi quyền).
   - **Data Model:** Thiết kế bảng trung gian `todo_shares` (chứa `id`, `todo_id`, `shared_with_user_id`, `permission_level`, `created_at`). Khai báo các ràng buộc Unique Key và Cascade Delete.
   - **API Design:** Định nghĩa các RESTful Endpoints (VD: `POST /todos/{id}/share`, `DELETE /todos/{id}/share/{user_id}`).
   - **Authorization & Edge Cases:** Xử lý logic chống chia sẻ cho chính mình (Self-sharing), ngăn trùng lặp thư mời, quản lý tranh chấp ghi (Concurrent updates) và đảm bảo xóa cache Redis ngay khi bị tước quyền.
   - **Out of Scope:** Định nghĩa rõ giới hạn (VD: Chưa làm tính năng gửi Email thông báo khi được share, chưa hỗ trợ share cho cả nhóm).

---

## 🐳 Task 3B: Docker & Infrastructure Optimization

**Mục tiêu:** Tối ưu hóa hệ thống container hiện tại (Docker). Theo đề bài, chúng ta cần hoàn thành ít nhất 3/5 hạng mục yêu cầu. Tôi đề xuất làm 4 hạng mục sau cho an toàn và toàn diện:

**Các bước thực hiện:**
1. **Healthchecks & Dependencies (Rất quan trọng):** 
   - Sửa file `docker-compose.yml`, thêm khối `healthcheck` cho service `postgres` (dùng `pg_isready`) và `redis` (dùng `redis-cli ping`).
   - Sửa service `backend`, cấu hình `depends_on` với điều kiện `condition: service_healthy` để backend chỉ chạy khi DB đã sẵn sàng thực sự.
2. **Thêm file `.dockerignore`:**
   - Tạo file `.dockerignore` cho cả thư mục `backend/` và `frontend/` nhằm loại bỏ các file không cần thiết (như `node_modules`, `venv`, `__pycache__`, `.env`) giúp giảm dung lượng context khi build image.
3. **Tối ưu Image Size (Multi-stage build / Slim Image):**
   - Đổi Base image của backend/frontend sang bản nhỏ gọn (ví dụ: `python:3.11-slim`, `node:20-alpine`).
4. **Tăng cường bảo mật (Security):**
   - Bổ sung cấu hình mật khẩu cho Redis thay vì để public mặc định.

---

## ⚡ Task 3C: Database Performance & Indexing Strategy

**Mục tiêu:** Tối ưu hiệu năng truy vấn dữ liệu cho hàng triệu bản ghi và viết Alembic Migration.

**Các bước thực hiện:**
1. **Phân tích hiệu năng (Explain Analyze):**
   - Viết các câu lệnh SQL kiểm tra hiệu năng (`EXPLAIN ANALYZE`) dựa trên các câu lệnh truy vấn chính của ứng dụng (Tìm todos theo `user_id`, sắp xếp theo `created_at`, lọc theo `completed`).
2. **Tạo Index bằng Alembic:**
   - Chạy lệnh sinh file migration mới (`alembic revision -m "add_todo_indexes"`).
   - Thiết kế Composite Index tối ưu cho bảng `todos`. Ví dụ tạo index trên cột `(user_id, completed, created_at)`.
3. **Chạy Benchmark & Lập bảng so sánh:**
   - Dùng script seed của dự án để nạp 1 triệu dòng dữ liệu vào DB local.
   - Chạy lại lệnh `EXPLAIN ANALYZE` và ghi chép thông số **Thời gian chạy trước khi có index (Before)** và **Sau khi có index (After)**.
4. **Viết báo cáo vào PR Description:**
   - Đưa bảng so sánh vào mô tả PR, kèm theo phần giải thích về sự đánh đổi (Tradeoffs) khi dùng Index (như tốn thêm dung lượng, làm chậm tốc độ thao tác Ghi/Thêm mới/Xóa).
