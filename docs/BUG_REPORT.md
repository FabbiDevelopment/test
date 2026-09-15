# Tier 1 Bug Hunting Report — Fabbi Assessment

Báo cáo chi tiết các lỗi bảo mật, logic nghiệp vụ, caching và state management được phát hiện trong hệ thống Fabbi Todo App theo đúng cấu trúc yêu cầu của bài đánh giá.

---

## Danh sách lỗi phát hiện & phương án xử lý

### 1. JWT Expiration Check Bypass (Critical)
- **Location**: `backend/app/core/security.py:56` trong hàm `verify_token`
- **Severity**: Critical
- **Reason**: Tùy chọn giải mã token thiết lập `options={"verify_exp": False}`, khiến thư viện `jose` bỏ qua hoàn toàn việc kiểm tra thời hạn hết hạn (`exp`) của token. Kẻ tấn công nếu thu thập được access token cũ đã hết hạn vẫn có thể tiếp tục sử dụng vô thời hạn để truy cập vào hệ thống, vi phạm nguyên tắc xác thực an toàn.
- **Fix Proposal**: Đổi thành `options={"verify_exp": True}` hoặc loại bỏ `options` để `jose` mặc định kiểm tra `exp`. Xử lý thêm ngoại lệ `jwt.ExpiredSignatureError`.

---

### 2. Missing Token Type Validation / Token Confusion (High)
- **Location**: `backend/app/api/deps.py:27-39` trong dependency `get_current_user`
- **Severity**: High
- **Reason**: Khi giải mã access token trong `get_current_user`, hệ thống chỉ lấy `sub` (user_id) mà không kiểm tra trường `"type"` trong payload. Do đó, người dùng có thể sử dụng Refresh Token (vốn có thời hạn dài nhiều ngày) để gọi trực tiếp các API bảo vệ thay cho Access Token (vốn chỉ nên sống 30 phút).
- **Fix Proposal**: Thêm kiểm tra bắt buộc `payload.get("type") == "access"`. Nếu khác `"access"`, ném ngoại lệ `HTTPException(status_code=401, detail="Invalid token type")`.

---

### 3. IDOR / BOLA in Todo Item Access (Critical)
- **Location**: `backend/app/api/v1/todos.py:88-155` trong các endpoint `get_todo`, `update_existing_todo`, `delete_existing_todo`
- **Severity**: Critical
- **Reason**: Khi người dùng gọi GET, PUT, DELETE theo `todo_id`, hệ thống chỉ kiểm tra todo có tồn tại trong cơ sở dữ liệu hay không (`if not todo: 404`), hoàn toàn không kiểm tra xem todo đó có thuộc về `current_user.id` hay không. Bất kỳ người dùng đã đăng nhập nào cũng có thể xem, chỉnh sửa hoặc xóa todo của người dùng khác nếu biết ID (Broken Object Level Authorization - OWASP API Top 1).
- **Fix Proposal**: Bổ sung kiểm tra sở hữu:
  ```python
  if todo.user_id != current_user.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Not authorized to access this todo",
      )
  ```

---

### 4. Shared Redis Cache Key Leaking Cross-User Data (Critical)
- **Location**: `backend/app/api/v1/todos.py:37` trong endpoint `get_todos`
- **Severity**: Critical
- **Reason**: Key cache danh sách todo được đặt cố định là `cache_key = "todos:list"`. Khi User A gọi API lấy danh sách todo của mình, dữ liệu của User A được lưu vào key này. Khi User B gọi API lấy danh sách, hệ thống đọc từ cache và trả về toàn bộ danh sách todo của User A cho User B. Đây là lỗ hổng rò rỉ dữ liệu người dùng cực kỳ nghiêm trọng.
- **Fix Proposal**: Đưa `user_id` và các tham số phân trang vào cache key:
  ```python
  cache_key = f"todos:user:{current_user.id}:page:{page}:size:{size}"
  ```

---

### 5. Missing & Faulty Cache Invalidation (High)
- **Location**: `backend/app/api/v1/todos.py:77-155` trong `create_new_todo`, `update_existing_todo`, `delete_existing_todo`
- **Severity**: High
- **Reason**: 
  - Trong `create_new_todo`: Không hề inject `redis` và không hề xóa cache sau khi tạo todo mới.
  - Trong `update_existing_todo` và `delete_existing_todo`: Dependency `redis` có được inject nhưng không hề có lệnh xóa hay làm mới cache tương ứng.
  - Hậu quả: Dữ liệu trên danh sách bị cũ (stale cache) sau các thao tác tạo mới, sửa hoặc xóa.
- **Fix Proposal**: Xây dựng hàm tiện ích xóa toàn bộ cache của user (`todos:user:{current_user.id}:*` hoặc xóa các key liên quan) và gọi đồng bộ tại các endpoint tạo, sửa, xóa todo.

---

### 6. Boolean Toggle Bug & Incomplete Partial Update (High)
- **Location**: `backend/app/api/v1/todos.py:121-134` trong hàm `update_existing_todo`
- **Severity**: High
- **Reason**:
  1. Đoạn code `if todo_data.completed:` coi giá trị `False` là falsy, dẫn đến việc khi client gửi `{ "completed": false }` để chuyển trạng thái từ hoàn thành về chưa hoàn thành, câu lệnh hoàn toàn bị bỏ qua và giá trị `completed` không bao giờ cập nhật về `False` được.
  2. Sử dụng `todo_data.model_dump()` thay vì `exclude_unset=True`, khiến các trường client không gửi bị gán `None` đè lên giá trị hiện có (ví dụ chỉ đổi title sẽ vô tình làm mất description).
- **Fix Proposal**:
  - Dùng `update_data = todo_data.model_dump(exclude_unset=True)`.
  - Kiểm tra `"completed" in update_data` để cập nhật cả `True` và `False`.

---

### 7. User Enumeration via Differentiated Error Messages (Medium)
- **Location**: `backend/app/api/v1/auth.py:53-65` trong endpoint `login`
- **Severity**: Medium
- **Reason**: API phân biệt rõ 2 thông báo lỗi: `detail="User not found"` (nếu email không tồn tại) và `detail="Incorrect password"` (nếu sai mật khẩu). Điều này giúp kẻ tấn công có thể rà quét (enumerate) danh sách email đã đăng ký tài khoản trong hệ thống.
- **Fix Proposal**: Thống nhất trả về một thông báo chung: `detail="Invalid email or password"` với mã HTTP 401.

---

### 8. Frontend React Query Cache Leak on Logout (Medium)
- **Location**: `frontend/src/features/auth/hooks/useAuth.ts:47-51` trong hàm `logout`
- **Severity**: Medium
- **Reason**: Khi người dùng bấm đăng xuất, hook chỉ xóa `access_token` và `refresh_token` trong `localStorage` mà không xóa cache của `@tanstack/react-query` trong bộ nhớ. Nếu một người dùng khác đăng nhập ngay sau đó trên cùng trình duyệt, họ có thể nhìn thấy dữ liệu todo của người dùng trước trong thoáng chốc trước khi query mới hoàn thành.
- **Fix Proposal**: Lấy `queryClient = useQueryClient()` và gọi `queryClient.clear()` khi đăng xuất.
