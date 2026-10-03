# Kế hoạch triển khai Tier 4: Optional Extension (Todo Tags, Filtering & Bulk Actions)

Tier 4 là một tính năng đầy đủ từ Backend đến Frontend (Full-stack feature) yêu cầu mở rộng kiến trúc hiện tại để hỗ trợ dán nhãn (Tags), lọc Todo nâng cao và thực hiện các thao tác hàng loạt (Bulk Actions).

Dưới đây là kế hoạch chi tiết chia làm 4 giai đoạn (Phases):

---

## 🟢 Giai đoạn 1: Database & Models (Backend)

1. **Thiết kế SQLAlchemy Models (`backend/app/models/tag.py` và cập nhật `todo.py`):**
   - Tạo model `Tag`: `id` (UUID), `user_id` (UUID FK), `name` (VARCHAR 50), `color` (VARCHAR 20), `created_at`, `updated_at`.
   - Tạo model liên kết nhiều-nhiều (Many-to-Many) `TodoTag`: `todo_id` (FK), `tag_id` (FK), Primary Key là `(todo_id, tag_id)`.
   - Thiết lập relationship giữa `User` -> `Tag`, `Todo` <-> `Tag`.

2. **Ràng buộc và Chỉ mục (Constraints & Indexes):**
   - Constraint: `UniqueConstraint` cho `(user_id, lower(name))` để đảm bảo tên tag là duy nhất với mỗi user, không phân biệt hoa thường.
   - Thêm Index cho `tags(user_id)`, `todo_tags(tag_id)`, `todo_tags(todo_id)`. (Index cho `todos` đã làm ở Tier 3C).

3. **Alembic Migration:**
   - Chạy lệnh `alembic revision --autogenerate -m "add_tags_and_bulk_actions"` và `alembic upgrade head`.

---

## 🟡 Giai đoạn 2: API Endpoints & Logic (Backend)

1. **Tag Management API (`backend/app/api/v1/tags.py`):**
   - Pydantic schemas: `TagCreate`, `TagUpdate`, `TagResponse`.
   - Endpoints: `GET /tags`, `POST /tags`, `PATCH /tags/{tag_id}`, `DELETE /tags/{tag_id}`.
   - Đảm bảo cơ chế phân quyền: User chỉ thao tác được trên Tag của mình. Xóa Tag phải tự động xóa dữ liệu ở bảng trung gian `todo_tags` (CASCADE hoặc thủ công).

2. **Cập nhật Todo API (`backend/app/api/v1/todos.py`):**
   - **Attach/Detach Tag:**
     - `POST /todos/{todo_id}/tags`: Gắn tag (check ownership cả Todo và Tag).
     - `DELETE /todos/{todo_id}/tags/{tag_id}`: Gỡ tag.
   - **Bulk Actions:**
     - `PATCH /todos/bulk-status`: Nhận `{ "todo_ids": [...], "completed": bool }`. Dùng SQLAlchemy Transaction để cập nhật hàng loạt và kiểm tra ownership.
   - **Lọc và Phân trang (Filtering & Pagination):**
     - Cập nhật `GET /todos` để nhận thêm query parameters: `status`, `tag_id`, `keyword`, `date_from`, `date_to`, `page`, `page_size`.
     - Cập nhật Redis Cache: Key cache giờ phải chứa chuỗi query parameters thay vì chỉ `user_id` để tránh cache conflict.
     - Cập nhật cơ chế Invalidate Cache (xóa cache khi có thay đổi liên quan đến bulk update, tags).

---

## 🟠 Giai đoạn 3: State Management & API Client (Frontend)

1. **Cập nhật API Layer (`frontend/src/features/todos/api/`):**
   - Thêm `tags.ts`: Chứa các hàm `useTags`, `useCreateTag`, `useUpdateTag`, `useDeleteTag` sử dụng `@tanstack/react-query`.
   - Mở rộng `todos.ts`:
     - Sửa `useTodos` để nhận thêm filter (status, keyword, v.v.). Query Key chuyển thành `['todos', filters]`.
     - Thêm `useBulkUpdateTodoStatus`, `useAttachTagToTodo`, `useDetachTagFromTodo`.

2. **Xử lý Cache Invalidation:**
   - Khi tạo/xóa Tag, hoặc đổi status hàng loạt, gọi `queryClient.invalidateQueries({ queryKey: ['todos'] })` và `['tags']`.
   - Clear cache khi Logout.

---

## 🔴 Giai đoạn 4: UI Components (Frontend)

1. **Thanh công cụ lọc (Filter Bar):**
   - Tạo component `TodoFilterBar`: Search input (keyword), Select (status), Multi-select (tags), Date Picker (từ ngày - đến ngày).
   - Nút "Clear Filters". Dùng local state hoặc URL Search Params để lưu state.

2. **Quản lý Tags (Tag Management UI):**
   - Một Modal hoặc Sidebar cho phép người dùng xem danh sách tag, tạo mới (chọn màu sắc), đổi tên và xóa tag. Dùng `react-hook-form` + `zod` để validate.

3. **Giao diện thao tác hàng loạt (Bulk Actions):**
   - Thêm Checkbox ở đầu mỗi Todo Item.
   - Có Checkbox "Select All".
   - Bảng điều khiển (Toolbar) hiện lên khi có ít nhất 1 item được chọn, chứa 2 nút: "Mark as Completed", "Mark as Active".

4. **Hiển thị Tag trên Todo Item:**
   - Trên mỗi Todo Item, thêm khu vực hiển thị các huy hiệu (badges) màu sắc cho các Tag. Thêm nút (ví dụ icon dấu +) để người dùng có thể gắn/gỡ tag nhanh.
