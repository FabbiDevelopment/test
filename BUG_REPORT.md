# Báo Cáo Lỗi — Fabbi Todo App

> **Khai báo sử dụng AI**: Dự án này sử dụng Claude Sonnet (Antigravity AI) để hỗ trợ phát hiện lỗi và đề xuất bản sửa. Tất cả kết quả đã được xác minh thủ công bằng cách đọc trực tiếp source code.

---

## Tổng Quan

| Mức độ | Số lượng |
|--------|----------|
| 🔴 Critical | 5 |
| 🟠 High | 6 |
| 🟡 Medium | 8 |
| 🔵 Low | 3 |
| **Tổng** | **22** |

---

## 🔴 Critical

---

### Issue #1: JWT Không Kiểm Tra Thời Gian Hết Hạn

- **Location**: `backend/app/core/security.py` — hàm `verify_token()`, dòng 56
- **Reason**: Tùy chọn `options={"verify_exp": False}` vô hiệu hóa hoàn toàn việc kiểm tra thời hạn của JWT token. Bất kỳ token nào — dù đã hết hạn từ lâu — đều vẫn được chấp nhận mãi mãi. Kẻ tấn công chỉ cần đánh cắp token một lần là có thể dùng vĩnh viễn.
- **Fix proposal**:
```python
# TRƯỚC (lỗi)
payload = jwt.decode(
    token, settings.JWT_SECRET,
    algorithms=[settings.JWT_ALGORITHM],
    options={"verify_exp": False},  # ← BỎ DÒNG NÀY
)

# SAU (đã sửa)
payload = jwt.decode(
    token, settings.JWT_SECRET,
    algorithms=[settings.JWT_ALGORITHM],
    # Không có options → jose tự kiểm tra exp
)
```

---

### Issue #2: Cache Key Không Phân Tách Theo `user_id`

- **Location**: `backend/app/api/v1/todos.py` — hàm `list_todos()`, dòng 37
- **Reason**: `cache_key = "todos:list"` dùng chung cho tất cả người dùng. User đầu tiên load trang sẽ ghi cache; tất cả user tiếp theo nhận đúng response đó, bất kể `user_id` của họ là ai. **User A nhìn thấy todos của User B.**
- **Fix proposal**:
```python
# TRƯỚC (lỗi)
cache_key = "todos:list"

# SAU (đã sửa)
cache_key = f"todos:list:{current_user.id}:{page}:{size}"
```

---

### Issue #3: Không Kiểm Tra Quyền Sở Hữu trên `GET /todos/{id}`

- **Location**: `backend/app/api/v1/todos.py` — hàm `get_todo()`, dòng 95–102
- **Reason**: Bất kỳ user đã đăng nhập nào cũng có thể đọc bất kỳ todo nào chỉ bằng cách biết UUID của nó. Endpoint truy vấn DB nhưng không kiểm tra `todo.user_id == current_user.id`.
- **Fix proposal**:
```python
todo = await get_todo_by_id(db, todo_id)
if not todo:
    raise HTTPException(status_code=404, detail="Todo not found")

# THÊM ĐOẠN KIỂM TRA NÀY
if todo.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Không có quyền truy cập todo này")
```

---

### Issue #4: Không Kiểm Tra Quyền Sở Hữu trên `PUT /todos/{id}`

- **Location**: `backend/app/api/v1/todos.py` — hàm `update_existing_todo()`, dòng 114
- **Reason**: Tương tự Issue #3. Bất kỳ user nào cũng có thể ghi đè nội dung todo của người khác — tiêu đề, mô tả, trạng thái hoàn thành.
- **Fix proposal**:
```python
if todo.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Không có quyền chỉnh sửa todo này")
```

---

### Issue #5: Không Kiểm Tra Quyền Sở Hữu trên `DELETE /todos/{id}`

- **Location**: `backend/app/api/v1/todos.py` — hàm `delete_existing_todo()`, dòng 145
- **Reason**: Bất kỳ user nào cũng có thể xóa todo của người khác. Kết hợp với Issue #3, đây là lỗ hổng cho phép phá hủy dữ liệu toàn hệ thống.
- **Fix proposal**:
```python
if todo.user_id != current_user.id:
    raise HTTPException(status_code=403, detail="Không có quyền xóa todo này")
```

---

## 🟠 High

---

### Issue #6: Login Trả `404` Khi Email Không Tồn Tại (User Enumeration)

- **Location**: `backend/app/api/v1/auth.py` — hàm `login()`, dòng 54–58
- **Reason**: Trả về `HTTP 404` khi email không có trong hệ thống cung cấp thông tin cho kẻ tấn công biết email nào đã đăng ký. Đây là lỗ hổng **user enumeration** — cho phép tấn công brute-force có chọn lọc.
- **Fix proposal**:
```python
# Dùng chung 401 cho cả hai trường hợp sai email VÀ sai mật khẩu
if not user or not verify_password(user_data.password, user.hashed_password):
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Email hoặc mật khẩu không đúng",
    )
```

---

### Issue #7: Refresh Token Không Kiểm Tra User Còn Tồn Tại

- **Location**: `backend/app/api/v1/auth.py` — hàm `refresh_token()`, dòng 92–98
- **Reason**: Sau khi xác thực loại token, endpoint cấp ngay access token mới mà không kiểm tra user còn tồn tại trong DB hay không. User đã bị xóa vẫn có thể lấy được token mới vô thời hạn nếu còn giữ refresh token chưa hết hạn.
- **Fix proposal**:
```python
user_id = payload.get("sub")
user = await get_user_by_id(db, uuid.UUID(user_id))
if user is None:
    raise HTTPException(status_code=401, detail="Tài khoản không còn tồn tại")

access_token = create_access_token(data={"sub": str(user.id)})
```

---

### Issue #8: `update_todo` Được Gọi Với Dict Rỗng `{}`

- **Location**: `backend/app/api/v1/todos.py` — hàm `update_existing_todo()`, dòng 132
- **Reason**: Endpoint gán thuộc tính thủ công qua `setattr`, sau đó gọi `update_todo(db, todo, {})`. Service lặp qua dict rỗng — là no-op. Nghiêm trọng hơn, `if todo_data.completed:` **bỏ qua khi `completed=False`**, khiến việc bỏ đánh dấu hoàn thành một todo là **bất khả thi**.
- **Fix proposal**:
```python
# Chỉ lấy các field mà client thực sự gửi lên
update_data = todo_data.model_dump(exclude_unset=True)
updated_todo = await update_todo(db, todo, update_data)
```

---

### Issue #9: Cache Không Bị Xóa Sau Khi Tạo / Cập Nhật / Xóa Todo

- **Location**: `backend/app/api/v1/todos.py` — các hàm `create_new_todo()`, `update_existing_todo()`, `delete_existing_todo()`
- **Reason**: `create_new_todo` hoàn toàn không có dependency Redis. Hàm update và delete có inject Redis nhưng không gọi `redis.delete(...)`. Kết quả: dữ liệu cũ từ cache được trả về tối đa 5 phút sau mỗi thay đổi.
- **Fix proposal**:
```python
# Thêm vào cuối mỗi mutation endpoint
await redis.delete(f"todos:list:{current_user.id}:*")
```
> ⚠️ **Lưu ý**: Redis `delete()` không hỗ trợ glob pattern mặc định. Trong production, dùng `SCAN` + `DELETE` hoặc thiết kế key theo cách xóa đơn giản hơn.

---

### Issue #10: N+1 Query — Truy Vấn User Cho Từng Todo

- **Location**: `backend/app/api/v1/todos.py` — hàm `list_todos()`, dòng 49–62
- **Reason**: Với mỗi todo trong danh sách, endpoint thực hiện một câu truy vấn `SELECT * FROM users WHERE id = ?` riêng biệt. Với 100 todos = 101 DB round-trips. Với 1,000 todos hiệu năng suy giảm nghiêm trọng.
- **Fix proposal**: Xóa vòng lặp truy vấn user. Trường `user_email` không được render ở frontend và là overhead không cần thiết:
```python
items = [
    TodoResponse(
        id=todo.id, title=todo.title, description=todo.description,
        completed=todo.completed, user_id=todo.user_id,
        created_at=todo.created_at, updated_at=todo.updated_at,
    )
    for todo in todos
]
```

---

### Issue #11: Thiếu Ràng Buộc `UNIQUE` Trên Cột `users.email`

- **Location**: `backend/alembic/versions/001_initial.py` dòng 29 + `backend/app/models/user.py` dòng 21
- **Reason**: Cột `email` không có unique constraint ở tầng database. App kiểm tra trùng bằng `SELECT` trước `INSERT` — đây là **TOCTOU race condition**. Hai request đăng ký đồng thời với cùng email đều qua kiểm tra và đều insert thành công. Lần đăng nhập kế tiếp sẽ gây lỗi `MultipleResultsFound`.
- **Fix proposal**:
```python
# Trong migration (001_initial.py)
sa.UniqueConstraint("email", name="uq_users_email")

# Trong ORM model (user.py)
email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
```

---

### Issue #12: Logout Không Xóa React Query Cache

- **Location**: `frontend/src/features/auth/api/auth.ts` — hàm `useLogout()`, `onSuccess`, dòng 51
- **Reason**: Khi logout, chỉ có token trong `localStorage` bị xóa. Cache in-memory của React Query vẫn giữ nguyên todos của user cũ. Nếu User B đăng nhập vào cùng tab trình duyệt, họ thấy ngay dữ liệu của User A cho đến khi query tự refetch.
- **Fix proposal**:
```typescript
onSuccess: () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  queryClient.clear(); // ← Xóa toàn bộ cache React Query
},
```

---

## 🟡 Medium

---

### Issue #13: Thiếu Index Trên Cột `todos.user_id`

- **Location**: `backend/alembic/versions/001_initial.py`
- **Reason**: Mọi câu truy vấn `GET /todos` đều có điều kiện `WHERE user_id = ?`. Không có index → full table scan. Với 1,000,000 todos (như seed script tạo), đây là vấn đề hiệu năng nghiêm trọng.
- **Fix proposal**:
```python
op.create_index("ix_todos_user_id", "todos", ["user_id"])
op.create_index("ix_todos_user_id_created_at", "todos", ["user_id", "created_at"])
```

---

### Issue #14: Kích Thước Trang Mặc Định 10,000

- **Location**: `frontend/src/features/todos/api/todos.ts` — `useTodos()` dòng 35
- **Reason**: `useTodos(1, 10000)` yêu cầu tới 10,000 bản ghi mỗi lần tải trang. Toàn bộ được serialize thành JSON, lưu vào Redis và truyền qua mạng. User có nhiều todo tự tạo tình trạng DoS cho chính mình.
- **Fix proposal**:
```typescript
export function useTodos(page: number = 1, size: number = 20) {
```

---

### Issue #15: React Query Key Thiếu Tham Số Phân Trang

- **Location**: `frontend/src/features/todos/api/todos.ts` — `useTodos()` dòng 37
- **Reason**: `queryKey: ["todos"]` giống nhau dù `page` hay `size` thay đổi thế nào. Khi chuyển trang, React Query thấy cùng key → không fetch mới → hiển thị dữ liệu trang cũ.
- **Fix proposal**:
```typescript
queryKey: ["todos", page, size],
```

---

### Issue #16: Optimistic Update Không Được Hoàn Tác Khi Gặp Lỗi

- **Location**: `frontend/src/features/todos/api/todos.ts` — `useUpdateTodo()` `onError`, dòng 95
- **Reason**: `onMutate` snapshot `previousTodos` và trả về trong `context`, nhưng `onError` bỏ qua hoàn toàn `context` — chỉ hiển thị toast. Giao diện vẫn ở trạng thái cập nhật optimistic (sai) sau khi request thất bại.
- **Fix proposal**:
```typescript
onError: (_err, _vars, context) => {
  // Phục hồi snapshot trước khi mutate
  if (context?.previousTodosMap) {
    context.previousTodosMap.forEach(([queryKey, data]) => {
      queryClient.setQueryData(queryKey, data);
    });
  }
  toast.error("Cập nhật thất bại");
},
```

---

### Issue #17: `key={index}` Thay Vì `key={todo.id}` Trong Danh Sách

- **Location**: `frontend/src/features/todos/components/TodoList.tsx` dòng 42
- **Reason**: Dùng index mảng làm React key gây lỗi reconciliation khi xóa hoặc sắp xếp lại item. State của checkbox có thể bị "rò rỉ" sang item khác sau khi xóa.
- **Fix proposal**:
```tsx
{todos.map((todo) => (
  <TodoItem key={todo.id} todo={todo} ... />
))}
```

---

### Issue #18: `VITE_API_URL=http://localhost:8000` Được Bake Vào Docker Image

- **Location**: `docker-compose.yml` dòng 42
- **Reason**: Biến `VITE_*` được Vite nhúng vào bundle tại thời điểm build, không phải runtime. Image frontend hard-code `localhost` làm host API. Trên môi trường thực (frontend và backend ở host khác nhau), mọi API call đều thất bại.
- **Fix proposal**: Dùng pattern `window._env_` để inject config lúc runtime, hoặc truyền build arg tường minh trong CI/CD pipeline.

---

### Issue #19: `allow_origins=["*"]` Kết Hợp `allow_credentials=True`

- **Location**: `backend/app/main.py` dòng 31–34
- **Reason**: Đây là vi phạm đặc tả CORS — trình duyệt từ chối gửi credentials khi `Access-Control-Allow-Origin` là wildcard. App dùng `Authorization: Bearer` header (không phải cookie) nên không bị ảnh hưởng runtime, nhưng cấu hình sai và gây rủi ro nếu sau này chuyển sang cookie-based auth.
- **Fix proposal**:
```python
allow_origins=["http://localhost:3000", "https://your-domain.com"]
```

---

### Issue #20: JWT Secret Mặc Định Là Chuỗi Đã Biết Trước

- **Location**: `backend/app/core/config.py` dòng 15 + `docker-compose.yml` dòng 27
- **Reason**: `JWT_SECRET = "super-secret-key-change-in-production"` được commit công khai trong repo. Nếu operator quên set env var, ứng dụng chạy với secret đã biết → mọi JWT đều có thể bị giả mạo.
- **Fix proposal**:
```python
# Không đặt giá trị mặc định → ValidationError nếu không cấu hình
JWT_SECRET: str
```

---

## 🔵 Low

---

### Issue #21: `DB_ECHO=True` Mặc Định — Log SQL Ra Production

- **Location**: `backend/app/core/config.py` dòng 9
- **Reason**: Ghi toàn bộ câu SQL vào stdout. Không phải vấn đề bảo mật nghiêm trọng ở đây, nhưng gây nhiễu log và overhead không cần thiết trong production.
- **Fix proposal**: `DB_ECHO: bool = False`

---

### Issue #22: Schema `UserCreate` Tái Sử Dụng Cho Endpoint Login

- **Location**: `backend/app/api/v1/auth.py` — `login()` dòng 48
- **Reason**: `UserCreate` là schema cho đăng ký nhưng cũng được dùng cho đăng nhập. Hai endpoint hiển thị cùng tên kiểu trong OpenAPI docs, gây nhầm lẫn.
- **Fix proposal**: Dùng schema `UserLogin` đã được định nghĩa sẵn trong `schemas/user.py`.

---

## Tóm Tắt Các Fix Đã Thực Hiện

| File | Thay đổi |
|------|----------|
| `backend/app/core/security.py` | Bỏ `verify_exp: False` — expiry được kiểm tra |
| `backend/app/api/v1/todos.py` | Cache key theo user; ownership check GET/PUT/DELETE; invalidate cache; sửa lỗi update dict rỗng; sửa `completed=False` |
| `backend/app/api/v1/auth.py` | Thống nhất 401; kiểm tra user tồn tại khi refresh |
| `backend/app/models/user.py` | `unique=True` trên email |
| `backend/alembic/versions/001_initial.py` | UNIQUE constraint + indexes |
| `backend/tests/test_auth.py` | +5 test bảo mật mới |
| `backend/tests/test_todos.py` | +6 test ownership và regression mới |
| `frontend/src/features/auth/api/auth.ts` | `queryClient.clear()` khi logout |
| `frontend/src/features/todos/api/todos.ts` | Query key đúng; page size 20; rollback optimistic |
| `frontend/src/features/todos/components/TodoList.tsx` | `key={todo.id}` |

## Kết Quả Test

```
21 passed, 0 failed — 10.43s
```

Tất cả 21 test case (bao gồm 11 test mới viết thêm) đều PASSED.
