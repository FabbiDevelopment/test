# Báo Cáo & Phân Tích Lỗi (Tier 1: Bug Hunting & Critical Fixes)

Tài liệu này tổng hợp toàn bộ các lỗi trọng yếu được phát hiện trong **Tier 1: Bug Hunting & Critical Fixes**, tuân thủ đúng cấu trúc báo cáo bắt buộc (*Location, Severity, Reason, Fix Proposal*).
---

## Bảng Tổng Quan Lỗi Phát Hiện

| Danh Mục | Tổng Số Lỗi | Nghiêm Trọng (Critical) | Cao (High) | Trung Bình (Medium) | Thấp (Low) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Backend (FastAPI / Database / Cache / Auth)** | 7 | 3 | 2 | 2 | 0 |
| **Frontend (React / TanStack Query / UI)** | 4 | 0 | 1 | 2 | 1 |
| **Tổng cộng** | **11** | **3** | **3** | **4** | **1** |

---

## I. Danh Sách Lỗi Backend (BE)

### Lỗi BE-01: Vô Hiệu Hóa Kiểm Tra Thời Hạn Hết Hạn Của Token JWT
* **Location**: `backend/app/core/security.py`, dòng 49–60 (hàm `verify_token`) & `backend/app/api/deps.py`, dòng 21–34 (hàm `get_current_user`)
* **Severity**: **Critical (Nghiêm trọng)**
* **Reason**: 
  Trong hàm `verify_token`, thư viện `jwt.decode` được truyền tùy chọn `options={"verify_exp": False}`. Điều này vô hiệu hóa hoàn toàn cơ chế kiểm tra thời gian hết hạn (`exp` claim) của token JWT. Hậu quả là token truy cập (access token) dù đã hết hạn vẫn được chấp nhận hợp lệ vĩnh viễn, cho phép kẻ xấu sử dụng lại các token cũ bị rò rỉ. Ngoài ra, hàm `get_current_user` không kiểm tra `payload.get("type") == "access"`, dẫn đến việc người dùng có thể gửi refresh token để gọi các API yêu cầu quyền truy cập thông thường.
* **Fix Proposal**:
  1. Loại bỏ cấu hình `options={"verify_exp": False}` (hoặc đặt rõ ràng thành `True`) trong `verify_token` để hàm bắt đúng ngoại lệ `jwt.ExpiredSignatureError` khi token hết hạn.
  2. Trong hàm `get_current_user`, kiểm tra thêm `payload.get("type") == "access"`; nếu không đúng thì trả về mã lỗi HTTP 401 Unauthorized.

---

### Lỗi BE-02: Lỗ Hổng Phân Quyền Đối Tượng (IDOR) Trên Các API Todo
* **Location**: `backend/app/api/v1/todos.py`, dòng 89–155 (các hàm `get_todo`, `update_existing_todo`, `delete_existing_todo`)
* **Severity**: **Critical (Nghiêm trọng)**
* **Reason**:
  Các endpoint xem chi tiết (`GET /todos/{todo_id}`), cập nhật (`PUT /todos/{todo_id}`), và xóa (`DELETE /todos/{todo_id}`) chỉ thực hiện tìm Todo theo `todo_id` qua câu lệnh `get_todo_by_id(db, todo_id)` mà hoàn toàn không kiểm tra quyền sở hữu (`todo.user_id == current_user.id`). Bất kỳ người dùng nào đã đăng nhập cũng có thể đọc trộm, chỉnh sửa hoặc xóa vĩnh viễn Todo riêng tư của người khác nếu biết UUID của Todo đó.
* **Fix Proposal**:
  Thêm bước kiểm tra quyền sở hữu ngay sau khi lấy Todo từ cơ sở dữ liệu:
  ```python
  if todo.user_id != current_user.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Not authorized to access this todo",
      )
  ```
  *(Hoặc trả về `404 Not Found` để tránh việc kẻ tấn công dò quét ID của người khác).*

---

### Lỗi BE-03: Dùng Chung Redis Cache Key Toàn Cục Gây Rò Rỉ Dữ Liệu Giữa Các Người Dùng
* **Location**: `backend/app/api/v1/todos.py`, dòng 37, 72 (các hàm `list_todos`, `create_new_todo`, `update_existing_todo`, `delete_existing_todo`)
* **Severity**: **Critical (Nghiêm trọng)**
* **Reason**:
  Key lưu cache trong Redis của hàm `list_todos` bị gán cứng cố định là: `cache_key = "todos:list"`.
  1. Khi **User A** tải danh sách Todo, danh sách của User A được lưu vào cache `"todos:list"`.
  2. Khi **User B** đăng nhập và gọi API `/todos`, hệ thống trả về ngay dữ liệu từ cache `"todos:list"` này $\rightarrow$ **User B thấy toàn bộ Todo của User A** (rò rỉ dữ liệu nghiêm trọng giữa các tài khoản).
  3. Key cache không chứa thông tin phân trang (`page`, `size`), làm sai lệch dữ liệu khi chuyển trang.
  4. Các API thêm/sửa/xóa (`POST`, `PUT`, `DELETE`) không hề có lệnh xóa/invalidation cache Redis, khiến dữ liệu cũ bị kẹt trong cache đến 5 phút (TTL = 300s).
* **Fix Proposal**:
  1. Phân chia namespace cho cache key theo từng người dùng và tham số phân trang:
     ```python
     cache_key = f"todos:list:{current_user.id}:page:{page}:size:{size}"
     ```
  2. Mỗi khi thực hiện tạo mới, cập nhật, hoặc xóa Todo, tiến hành xóa (invalidate) các key cache liên quan của user đó trong Redis (ví dụ: `redis.delete(...)` hoặc xóa theo pattern của user).

---

### Lỗi BE-04: Lỗi Logic Không Thể Bỏ Chọn Hoàn Thành (Boolean Toggle Bug)
* **Location**: `backend/app/api/v1/todos.py`, dòng 123–124 (hàm `update_existing_todo`)
* **Severity**: **High (Cao)**
* **Reason**:
  Logic cập nhật trạng thái hoàn thành đang dùng phép kiểm tra chân trị (truthy check):
  ```python
  if todo_data.completed:
      todo.completed = todo_data.completed
  ```
  Khi người dùng muốn đổi trạng thái từ hoàn thành (`true`) về chưa hoàn thành (`false`), payload gửi lên là `{ "completed": false }`. Trong Python, `if False:` sẽ bị bỏ qua và khối lệnh không được thực thi. Do đó, một Todo khi đã đánh dấu hoàn thành thì vĩnh viễn không thể uncheck lại được.
* **Fix Proposal**:
  Kiểm tra điều kiện khác `None`:
  ```python
  if todo_data.completed is not None:
      todo.completed = todo_data.completed
  ```

---

### Lỗi BE-05: Mất Dữ Liệu Description Khi Thực Hiện Cập Nhật Từng Phần (Partial Update)
* **Location**: `backend/app/api/v1/todos.py`, dòng 121, 129–131 (hàm `update_existing_todo`)
* **Severity**: **High (Cao)**
* **Reason**:
  Hàm sử dụng `update_data = todo_data.model_dump()`. Mặc định Pydantic v2 sẽ xuất ra cả những trường không được truyền vào request với giá trị `None`. Ví dụ, nếu client chỉ muốn sửa tiêu đề và gửi `{ "title": "Tiêu đề mới" }`, biến `update_data` vẫn chứa `{ "title": "Tiêu đề mới", "description": None }`. Vì điều kiện `"description" in update_data` luôn trả về `True`, trường `todo.description` hiện có trong database bị đè thành `None` (mất dữ liệu mô tả của người dùng).
* **Fix Proposal**:
  Sử dụng `todo_data.model_dump(exclude_unset=True)` để chỉ lấy đúng những trường được gửi lên trong request payload.

---

### Lỗi BE-06: Lỗi Hiệu Năng N+1 Query Khi Lấy Danh Sách Todo
* **Location**: `backend/app/api/v1/todos.py`, dòng 48–62 (hàm `list_todos`)
* **Severity**: **Medium (Trung bình)**
* **Reason**:
  Trong vòng lặp duyệt qua các `todos`, code bắn thêm một truy vấn riêng biệt vào database cho từng item để lấy thông tin email của user:
  ```python
  for todo in todos:
      user_result = await db.execute(select(User).where(User.id == todo.user_id))
  ```
  Nếu trang có 20 todos, hệ thống sẽ thực hiện thêm 20 câu truy vấn thừa thãi vào database (vấn đề N+1 query). Trong khi đó, toàn bộ danh sách todos này vốn dĩ đã thuộc về `current_user`.
* **Fix Proposal**:
  Tận dụng trực tiếp thông tin người dùng đang đăng nhập: `user_email=current_user.email` mà không cần query lại database trong vòng lặp.

---

### Lỗi BE-07: Thiếu Mệnh Đề ORDER BY Gây Xáo Trộn Thứ Tự Danh Sách Khi Cập Nhật (Non-Deterministic Ordering)
* **Location**: `backend/app/services/todo_service.py`, dòng 31 (hàm `get_todos`)
* **Severity**: **Medium (Trung bình)**
* **Reason**:
  Câu truy vấn lấy danh sách Todo phân trang hiện tại hoàn toàn không có mệnh đề `ORDER BY`:
  ```python
  query = select(Todo).where(Todo.user_id == user_id).offset(skip).limit(limit)
  ```
  Trong PostgreSQL (cơ chế MVCC), mỗi khi một Todo được cập nhật (ví dụ bấm tick hoàn thành hoặc sửa tiêu đề), cơ sở dữ liệu sẽ ghi bản ghi mới vào một vị trí vật lý khác trong heap table. Do không có `ORDER BY` cố định, danh sách Todo trả về cho client sẽ bị xáo trộn vị trí ngẫu nhiên, khiến các hàng trên giao diện bị nhảy loạn xạ và đảo lộn trật tự sau mỗi thao tác.
* **Fix Proposal**:
  Bổ sung mệnh đề sắp xếp cố định theo thời gian tạo mới nhất và ID giảm dần theo đúng quy chuẩn đề bài tại [README.md (dòng 194)](file:///d:/tbui/test/README.md#L194):
  ```python
  query = (
      select(Todo)
      .where(Todo.user_id == user_id)
      .order_by(Todo.created_at.desc(), Todo.id.desc())
      .offset(skip)
      .limit(limit)
  )
  ```

---

## II. Danh Sách Lỗi Frontend (FE)

### Lỗi FE-01: Không Xóa Cache React Query Khi Đăng Xuất (Rò Rỉ Dữ Liệu Phiên Làm Việc)
* **Location**: `frontend/src/features/auth/hooks/useAuth.ts`, dòng 23–35 & `frontend/src/features/auth/api/auth.ts`, dòng 46–56
* **Severity**: **High (Cao)**
* **Reason**:
  Khi người dùng đăng xuất, ứng dụng chỉ xóa `access_token` và `refresh_token` trong `localStorage`. Bộ nhớ RAM lưu trữ query cache của TanStack React Query (`queryClient`) hoàn toàn không được dọn dẹp. Nếu User A đăng xuất và User B đăng nhập vào trên cùng một trình duyệt (không tải lại trang), User B sẽ nhìn thấy ngay danh sách Todo và thông tin của User A còn lưu trong cache (`["todos"]`, `["currentUser"]`).
* **Fix Proposal**:
  Gọi `queryClient.clear()` (hoặc `queryClient.removeQueries()`) khi đăng xuất thành công để xóa sạch toàn bộ dữ liệu tạm:
  ```typescript
  import { queryClient } from "@/lib/queryClient";

  // Trong callback onSuccess / onError của logout:
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  queryClient.clear();
  ```

---

### Lỗi FE-02: Form Edit Không Đồng Bộ Dữ Liệu Khi Chuyển Giữa Các Todo Khác Nhau
* **Location**: `frontend/src/features/todos/components/TodoForm.tsx`, dòng 32–38
* **Severity**: **Medium (Trung bình)**
* **Reason**:
  Hook `useForm<TodoFormData>` khởi tạo `defaultValues` từ prop `todo` truyền vào. Trong React Hook Form, `defaultValues` chỉ được tính toán một lần duy nhất khi component mount. Khi người dùng bấm "Sửa" Todo số 1, đóng dialog, rồi bấm "Sửa" Todo số 2, form vẫn giữ nguyên tiêu đề và mô tả của Todo số 1 thay vì hiển thị dữ liệu của Todo số 2.
* **Fix Proposal**:
  Thêm hook `useEffect` gọi `reset({ title: todo?.title || "", description: todo?.description || "" })` mỗi khi prop `todo` hoặc trạng thái `open` thay đổi (hoặc truyền prop `key={todo?.id || "new"}` vào component `<TodoForm />` để ép React remount).

---

### Lỗi FE-03: Thiếu Cơ Chế Rollback Cho Optimistic Update Khi Gặp Lỗi
* **Location**: `frontend/src/features/todos/api/todos.ts`, dòng 76–101 (hàm `useUpdateTodo`)
* **Severity**: **Medium (Trung bình)**
* **Reason**:
  Hàm `onMutate` lưu lại snapshot `previousTodos` và cập nhật trực tiếp cache trên giao diện trước khi server phản hồi, sau đó trả về `{ previousTodos }`. Tuy nhiên hàm `onError` chỉ hiển thị thông báo lỗi bằng toast mà không hề khôi phục lại `previousTodos`. Nếu server từ chối cập nhật (ví dụ mất kết nối mạng, lỗi 403 hoặc lỗi 500), màn hình vẫn hiển thị trạng thái sửa đổi sai lệch cho đến khi người dùng refresh lại trang.
* **Fix Proposal**:
  Bổ sung rollback trong `onError`:
  ```typescript
  onError: (_err, _variables, context) => {
    if (context?.previousTodos) {
      queryClient.setQueryData(["todos"], context.previousTodos);
    }
    toast.error("Failed to update todo");
  },
  ```

---

### Lỗi FE-04: Dùng Index Của Mảng Làm Key Trong Danh Sách React (Anti-Pattern)
* **Location**: `frontend/src/features/todos/components/TodoList.tsx`, dòng 42
* **Severity**: **Low (Thấp)**
* **Reason**:
  Dòng `<TodoItem key={index} ... />` sử dụng chỉ mục mảng (`index`) làm key nhận diện của React. Khi Todo bị xóa, sắp xếp lại hoặc lọc, React Reconciliation sẽ liên kết nhầm state giữa các phần tử DOM, gây ra lỗi hiển thị nhấp nháy hoặc checkbox nhảy sai vị trí.
* **Fix Proposal**:
  Sử dụng ID duy nhất của Todo làm key: `key={todo.id}`.
