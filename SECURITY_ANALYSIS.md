# Báo cáo Phân tích Lỗi & Bảo mật Codebase (Tier 1 Report)

**Dự án:** Fabbi Todo App (FastAPI Backend + React Frontend)  
**Ngày cập nhật:** 19/09/2026  

---

## 1. Kết luận Tổng quan

* **Mã độc & Khai thác / Đánh cắp thông tin cá nhân: KHÔNG CÓ.**
  * Dự án hoàn toàn an toàn đối với dữ liệu máy tính của bạn, không có phần mềm độc hại (malware), keylogger hay backdoor.
  * Không có bất kỳ kết nối mạng ngầm nào gửi thông tin cá nhân ra máy chủ bên ngoài.

* **Lỗ hổng bảo mật & Lỗi lập trình (Tier 1 Bugs): CÓ.**
  * Tồn tại các lỗi quan trọng về xác thực JWT, rò rỉ dữ liệu qua Redis cache, phân quyền đối tượng (IDOR), lỗi logic cập nhật trạng thái Todo và lỗi quản lý cache ở phía Frontend.

---

## 2. Báo cáo Chi tiết các Lỗi theo Định dạng Tier 1

### 🔴 Bug 1: Bỏ qua kiểm tra thời gian hết hạn của JWT Access Token
* **Location**: [backend/app/core/security.py](file:///c:/Users/Boot10/Desktop/test/test/backend/app/core/security.py#L56) (`verify_token`)
* **Severity**: Critical
* **Reason**: Hàm `jwt.decode` cài đặt `options={"verify_exp": False}` làm hệ thống chấp nhận cả các Token đã hết hạn. Kẻ tấn công sở hữu token cũ có thể truy cập hệ thống vô thời hạn.
* **Fix Proposal**: Loại bỏ cài đặt `options={"verify_exp": False}` để thư viện `jose` tự động từ chối và giải mã lỗi đối với các JWT Token đã quá hạn.

### 🔴 Bug 2: Rò rỉ dữ liệu danh sách Todo giữa các User qua Redis Cache
* **Location**: [backend/app/api/v1/todos.py](file:///c:/Users/Boot10/Desktop/test/test/backend/app/api/v1/todos.py#L37-L74) (`list_todos`)
* **Severity**: Critical
* **Reason**: Key cache Redis được đặt tên cố định là `"todos:list"`. Khi User A lấy danh sách todo, dữ liệu của A được lưu dưới key này. Ngay sau đó User B đăng nhập và gửi request sẽ nhận được toàn bộ dữ liệu Todo của User A từ Redis cache. Đồng thời, khi tạo/sửa/xóa todo không hề xóa bớt cache cũ.
* **Fix Proposal**: Thay đổi định dạng cache key có gắn `user_id` và thông số phân trang, ví dụ: `todos:{current_user.id}:list:page_{page}_size_{size}`. Thực hiện xóa các key cache liên quan của user khi có thao tác tạo mới, cập nhật hoặc xóa Todo.

### 🔴 Bug 3: Thiếu kiểm tra phân quyền sở hữu Todo (Lỗ hổng IDOR)
* **Location**: [backend/app/api/v1/todos.py](file:///c:/Users/Boot10/Desktop/test/test/backend/app/api/v1/todos.py#L88-L154) (`get_todo`, `update_existing_todo`, `delete_existing_todo`)
* **Severity**: Critical
* **Reason**: Khi người dùng xem, sửa hoặc xóa một Todo theo `todo_id`, API chỉ tìm todo theo `id` mà không kiểm tra xem `todo.user_id` có trùng với `current_user.id` hay không. Bất kỳ người dùng đã đăng nhập nào cũng có thể đọc, sửa hoặc xóa Todo của người khác nếu biết ID (UUID).
* **Fix Proposal**: Bổ sung điều kiện kiểm tra quyền sở hữu `if todo.user_id != current_user.id: raise HTTPException(status_code=403, detail="Not authorized to access this todo")` hoặc cập nhật query DB chỉ lấy todo thuộc về `current_user.id`.

### 🟠 Bug 4: Không thể chuyển trạng thái `completed` từ `true` về `false` và lỗi mất dữ liệu khi Update
* **Location**: [backend/app/api/v1/todos.py](file:///c:/Users/Boot10/Desktop/test/test/backend/app/api/v1/todos.py#L123-L132) (`update_existing_todo`)
* **Severity**: High
* **Reason**: 
  1. Câu lệnh `if todo_data.completed:` sẽ trả về `False` khi client muốn cập nhật `completed = False`, làm cho giá trị `false` bị bỏ qua không lưu.
  2. Dòng `updated_todo = await update_todo(db, todo, {})` truyền một dictionary rỗng `{}` vào hàm `update_todo`, khiến các trường khác (như `title`, `description`) không được cập nhật vào cơ sở dữ liệu.
* **Fix Proposal**: Sửa điều kiện kiểm tra thành `if todo_data.completed is not None: todo.completed = todo_data.completed`, đồng thời truyền đúng dict chứa dữ liệu cập nhật `update_data` vào hàm `update_todo(db, todo, update_data)`.

### 🟡 Bug 5: Sử dụng Index của mảng làm `key` trong React Component
* **Location**: [frontend/src/features/todos/components/TodoList.tsx](file:///c:/Users/Boot10/Desktop/test/test/frontend/src/features/todos/components/TodoList.tsx#L42) (`TodoList`)
* **Severity**: Medium
* **Reason**: Việc dùng `key={index}` khiến React render sai hoặc bị xáo trộn UI khi các phần tử Todo trong danh sách bị thay đổi vị trí, xóa hoặc đảo trạng thái.
* **Fix Proposal**: Thay thế `key={index}` bằng `key={todo.id}` để đảm bảo mỗi Todo Item có một key duy nhất và ổn định.

### 🟡 Bug 6: Không xóa React Query Cache khi người dùng Đăng xuất (Logout)
* **Location**: [frontend/src/features/auth/hooks/useAuth.ts](file:///c:/Users/Boot10/Desktop/test/test/frontend/src/features/auth/hooks/useAuth.ts#L23-L35) (`logout`)
* **Severity**: Medium
* **Reason**: Khi người dùng nhấn Logout, ứng dụng chỉ xóa token khỏi `localStorage` nhưng vẫn giữ nguyên React Query Cache trong bộ nhớ RAM. Nếu tài khoản khác đăng nhập ngay sau đó trên cùng phiên làm việc, dữ liệu của tài khoản cũ có thể hiển thị tạm thời trên giao diện.
* **Fix Proposal**: Thêm `queryClient.clear()` vào hàm xử lý `logout` để làm sạch toàn bộ cache dữ liệu phía Frontend.

### 🟡 Bug 7: Kích thước trang mặc định quá lớn ở phía Frontend
* **Location**: [frontend/src/features/todos/api/todos.ts](file:///c:/Users/Boot10/Desktop/test/test/frontend/src/features/todos/api/todos.ts#L35) (`useTodos`)
* **Severity**: Low
* **Reason**: Frontend yêu cầu mặc định `size = 10000`, không tương thích với logic phân trang mặc định (20 items/page) của Backend, gây dư thừa tải dữ liệu không cần thiết.
* **Fix Proposal**: Điều chỉnh tham số mặc định `size` về `20` cho đồng bộ với Backend.
