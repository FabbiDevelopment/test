  ### 1. Tổng quan yêu cầu của Tier 1 trong README.md
  Tier 1 yêu cầu:
  1. Tìm & báo cáo các lỗi quan trọng nhất theo cấu trúc chuẩn:
      • Location: đường dẫn file và số dòng / tên hàm.
      • Severity: Critical / High / Medium / Low.
      • Reason: Tại sao là lỗi (security flaw, data leak, regression, v.v.).
      • Fix Proposal: Giải pháp hoặc code patch khắc phục.
  2. Triển khai sửa ít nhất 5 lỗi trọng yếu (tối thiểu 2 backend và 1 frontend).
  3. Trọng tâm: Tính đúng đắn (correctness), phân quyền (authorization) và cô lập dữ liệu (data isolation), tránh các sửa đổi giao
  diện nhỏ nhặt.
  ──────
  ### 2. Danh sách các lỗi phát hiện được trong codebase
   STT | Lỗi phát hiện                                                       | Thành phần | Mức độ   | Nhóm vấn đề
  -----|---------------------------------------------------------------------|------------|----------|--------------------------------
   1   | JWT không kiểm tra hạn hết hạn token (verify_exp: False)            | Backend    | Critical | Authentication / Security
   2   | BOLA / IDOR: Không kiểm tra quyền sở hữu khi xem, sửa, xoá Todo     | Backend    | Critical | Authorization / Data Isolation
   3   | Redis cache key tĩnh todos:list gây rò rỉ dữ liệu chéo giữa các     | Backend    | Critical | Caching / Data Leak
       | user                                                                |            |          |
   4   | Không xóa/invalidate cache Redis khi tạo, sửa, xoá Todo             | Backend    | High     | Caching / Stale Data
   5   | Không thể chuyển trạng thái Todo từ Hoàn thành (True) về Chưa hoàn  | Backend    | High     | Business Logic
       | thành (False)                                                       |            |          |
   6   | Cập nhật một phần (partial update) xóa mất trường description       | Backend    | High     | Data Loss / Pydantic Logic
   7   | Lộ thông tin người dùng (User Enumeration) tại endpoint /auth/login | Backend    | Medium   | Security
   8   | N+1 Query trong vòng lặp lấy danh sách Todo                         | Backend    | Medium   | Performance / DB
   9   | Đăng xuất không dọn dẹp cache React Query (queryClient.clear())     | Frontend   | High     | Data Leak / Client State
   10  | Dùng mảng index làm key trong danh sách Todo                        | Frontend   | Medium   | React Rendering / UI State
   11  | Optimistic update không rollback khi request cập nhật thất bại      | Frontend   | Medium   | State Inconsistency
   12  | Query key useTodos thiếu tham số phân trang (page, size) & tải mặc  | Frontend   | Medium   | Caching / Performance
       | định 10.000 bản ghi                                                 |            |          |
  ──────
  ### 3. Chi tiết từng lỗi & Giải pháp triển khai (Fix Proposal)
  #### 3.1. Nhóm Backend
  ──────
  #### Lỗi 1: Bỏ qua kiểm tra thời gian hết hạn của JWT Token (Token Expiration Ignored)
  • Location: security.py:49-61 trong hàm verify_token.
  • Severity: Critical
  • Reason: Hàm jwt.decode() thiết lập options={"verify_exp": False}. Khi đó các JWT access token hoặc refresh token đã hết hạn vẫn
  được coi là hợp lệ mãi mãi. Kẻ tấn công nếu có được token cũ sẽ duy trì quyền truy cập vĩnh viễn.
  • Fix Proposal: Xóa bỏ options={"verify_exp": False} để thư viện mặc định validate trường exp:
    def verify_token(token: str) -> dict[str, Any] | None:
        """Verify and decode a JWT token."""
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET,
                algorithms=[settings.JWT_ALGORITHM],
            )
            return payload
        except JWTError:
            return None
  ──────
  #### Lỗi 2: BOLA / IDOR - Không kiểm tra quyền sở hữu Todo (User A thao tác Todo của User B)
  • Location: todos.py:90-153 trong get_todo, update_existing_todo, delete_existing_todo.
  • Severity: Critical
  • Reason: Các endpoint chỉ kiểm tra if not todo: raise 404, không hề kiểm tra todo.user_id == current_user.id. Bất kỳ user đã đăng
  nhập nào cũng có thể đọc, sửa nội dung hoặc xoá Todo của người khác nếu biết được todo_id.
  • Fix Proposal: Thêm kiểm tra quyền sở hữu (trả về 403 Forbidden hoặc 404 Not Found để tránh lộ ID) trước khi cho phép đọc/sửa/xoá:
    if todo.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this todo",
        )
  ──────
  #### Lỗi 3: Redis Cache Key dùng chung todos:list gây rò rỉ dữ liệu chéo (Cross-User Data Leak)

  • Location: todos.py:37-43 trong list_todos.
  • Severity: Critical
  • Reason: Key Redis được hardcode cố định cache_key = "todos:list". Khi User A gọi danh sách, danh sách của User A được lưu vào key
  này. Khi User B gọi danh sách ngay sau đó, User B sẽ nhận toàn bộ Todo của User A từ cache! Đồng thời key này không phân biệt tham
  số phân trang page và size.
  • Fix Proposal: Đưa user_id và các tham số phân trang vào cache key:

    cache_key = f"todos:list:{current_user.id}:page:{page}:size:{size}"
  ──────
  #### Lỗi 4: Thiếu Cache Invalidation khi Tạo, Sửa, Xoá Todo

  • Location: todos.py:77-154 trong create_new_todo, update_existing_todo, delete_existing_todo.
  • Severity: High
  • Reason: create_new_todo không inject Redis client, còn update_existing_todo và delete_existing_todo inject nhưng không hề gọi xoá
  cache. Dẫn tới dữ liệu mới cập nhật không xuất hiện trên UI suốt CACHE_TTL = 300 (5 phút).
  • Fix Proposal: Inject redis: RedisClient = Depends(get_redis) vào create_new_todo và viết hàm tiện ích xoá các key cache của user
  khi dữ liệu thay đổi:

    async def invalidate_user_todos_cache(redis: RedisClient, user_id: uuid.UUID):
        # Xoá pattern hoặc quản lý version key cho user
        keys = await redis.client.keys(f"todos:list:{user_id}:*")
        if keys:
            await redis.client.delete(*keys)
  ──────
  #### Lỗi 5: Lỗi logic cập nhật trạng thái completed từ True về False

  • Location: todos.py:123-124 trong update_existing_todo.
  • Severity: High
  • Reason: Câu lệnh if todo_data.completed: kiểm tra truthiness. Khi client truyền completed: false, giá trị này mang tính chất falsy
  trong Python, khiến nhánh if bị bỏ qua và không bao giờ gán todo.completed = False.
  • Fix Proposal: Kiểm tra giá trị khác None:

    if todo_data.completed is not None:
        todo.completed = todo_data.completed
  ──────
  #### Lỗi 6: Partial Update làm mất dữ liệu description (Data Loss)

  • Location: todos.py:121-133 trong update_existing_todo.
  • Severity: High
  • Reason: Sử dụng todo_data.model_dump() mà không có exclude_unset=True. Khi client chỉ gửi payload { "title": "New Title" },
  Pydantic sinh ra dict {"title": "New Title", "description": None, "completed": None}. Dòng if "description" in update_data: sẽ luôn
  đúng (do key có tồn tại với giá trị None), ghi đè todo.description hiện tại thành None. Đồng thời ở dòng 132 lại gọi update_todo(db,
  todo, {}) với dict rỗng.
  • Fix Proposal: Dùng exclude_unset=True:

    update_dict = todo_data.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(todo, key, value)
    await db.flush()
    await db.refresh(todo)
  ──────
  #### Lỗi 7: User Enumeration Vulnerability ở API Login

  • Location: auth.py:54-66 trong login.
  • Severity: Medium
  • Reason: Trả về 404 Not Found ("User with this email not found") nếu sai email, nhưng lại trả về 401 Unauthorized ("Incorrect
  password") nếu sai mật khẩu (vi phạm kịch bản TC-02 trong TEST_PLAN_TEMPLATE.md). Điều này cho phép kẻ tấn công dò tìm xem email nào
  đã đăng ký trong hệ thống.
  • Fix Proposal: Dùng hàm auth_service.py:33-39 đã có sẵn trong auth_service.py hoặc trả về lỗi chung 401 Unauthorized với thông điệp
  "Invalid email or password".
  ──────
  #### Lỗi 8: N+1 Query khi lấy danh sách Todo

  • Location: todos.py:48-50 trong list_todos.
  • Severity: Medium
  • Reason: Chạy truy vấn SQL riêng rẽ select(User).where(User.id == todo.user_id) lặp lại trong vòng lặp for cho từng Todo chỉ để lấy
  user_email. Với 20 items trên 1 trang sẽ sinh ra 21 câu lệnh SQL. Trong khi tất cả Todo đều thuộc về current_user.
  • Fix Proposal: Gán trực tiếp user_email=current_user.email.
  ──────
  #### 3.2. Nhóm Frontend
  ──────
  #### Lỗi 9: Đăng xuất không dọn sạch cache của React Query (Client Data Leak)

  • Location: auth.ts:46-56 & useAuth.ts:23-35.
  • Severity: High
  • Reason: Khi user bấm Logout, hàm chỉ xoá token trong localStorage. Cache trong bộ nhớ của React Query (queryClient) đối với
  ["todos"] và ["currentUser"] không hề được reset. Nếu User B đăng nhập tiếp theo trên cùng trình duyệt mà không refresh trang, User
  B có thể nhìn thấy dữ liệu Todo của User A còn lưu trong React Query.
  • Fix Proposal: Gọi queryClient.clear() khi logout thành công:

    export function useLogout() {
      return useMutation({
        mutationFn: async () => {
          await api.post("/auth/logout");
        },
        onSuccess: () => {
          localStorage.removeItem("access_token");
          localStorage.removeItem("refresh_token");
          queryClient.clear();
        },
      });
    }
  ──────
  #### Lỗi 10: Sử dụng index của mảng làm React key trong TodoList

  • Location: TodoList.tsx:42.
  • Severity: Medium
  • Reason: todos.map((todo, index) => <TodoItem key={index} ... />) dùng chỉ số mảng làm key. Khi xoá, thêm hoặc toggle item, React
  Virtual DOM reconcile sai component con, gây lag, nháy UI hoặc giữ sai local state checkbox/form.
  • Fix Proposal: Dùng ID định danh duy nhất của Todo:

    <TodoItem
      key={todo.id}
      todo={todo}
      index={index}
      onToggle={handleToggle}
      onEdit={handleEdit}
      onDelete={handleDelete}
    />
  ──────
  #### Lỗi 11: Thiếu cơ chế Rollback khi Optimistic Update thất bại

  • Location: todos.ts:95-97 trong useUpdateTodo.
  • Severity: Medium
  • Reason: Trong onMutate đã lưu lại previousTodos, nhưng hook onError chỉ hiện toast thông báo lỗi mà không rollback lại
  previousTodos vào queryClient. Nếu server trả lỗi (403, 500, v.v.), giao diện vẫn hiển thị trạng thái đã đổi cho tới khi user load
  lại trang.
  • Fix Proposal:

    onError: (_error, _variables, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(["todos"], context.previousTodos);
      }
      toast.error("Failed to update todo");
    },
  ──────
  #### Lỗi 12: Query Key useTodos thiếu phân trang & tải mặc định 10.000 bản ghi

  • Location: todos.ts:35-37.
  • Severity: Medium
  • Reason: useTodos(page = 1, size = 10000) dùng queryKey: ["todos"] không gắn page và size, dẫn đến việc các trang khác nhau dùng
  chung một cache. Việc truyền size: 10000 tạo tải lớn lên database và đường truyền mạng.
  • Fix Proposal: Đưa params vào query key và đặt size mặc định hợp lý (ví dụ 20 theo backend):

    export function useTodos(page: number = 1, size: number = 20) {
      return useQuery({
        queryKey: ["todos", { page, size }],
        queryFn: async (): Promise<TodoListResponse> => {
          const response = await api.get("/todos", { params: { page, size } });
          return response.data;
        },
      });
    }
  ──────
  ### 4. Đề xuất 5 lỗi trọng tâm để triển khai cho Tier 1 (Đạt chuẩn 30 điểm)

  Theo yêu cầu của README (tối thiểu 5 lỗi, gồm ít nhất 2 Backend và 1 Frontend, ưu tiên bảo mật & cách ly dữ liệu):

  1. [Backend] Lỗi 1 - Enforce JWT Token Expiration: Sửa verify_exp: True trong security.py.
  2. [Backend] Lỗi 2 - BOLA / IDOR Check: Thêm kiểm tra todo.user_id == current_user.id trong todos.py.
  3. [Backend] Lỗi 3 & 4 - User-scoped Redis Cache & Cache Invalidation: Gắn current_user.id vào cache key và invalidate cache khi
  create/update/delete trong todos.py.
  4. [Backend] Lỗi 5 & 6 - Fix Boolean Toggle & Partial Update: Sửa if todo_data.completed is not None và dùng
  model_dump(exclude_unset=True) trong todos.py.
  5. [Frontend] Lỗi 9 - Clear Query Cache on Logout: Thêm queryClient.clear() vào auth.ts và sửa key={todo.id} trong TodoList.tsx.