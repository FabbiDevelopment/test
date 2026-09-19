# AI Assistant Usage & Prompt Log

## Công cụ sử dụng

Claude (Anthropic) qua giao diện chat, dùng theo mô hình: đọc/phân tích code
trực tiếp trong phiên chat, sau đó viết prompt cụ thể để dán vào IDE (đã dùng
AI code assistant khác trong IDE để áp dụng thay đổi thực tế vào code), rồi
quay lại chat để kiểm chứng kết quả trước khi commit.

## Nguyên tắc làm việc

Mọi thay đổi do AI đề xuất đều được tự kiểm chứng bằng phương pháp "ố ý tình
đưa bug/lỗi trở lại, chạy test xem có fail đúng không, rồi khôi phục fix và
xác nhận pass lại" trước khi commit — áp dụng cho toàn bộ 8 bug và các phần
cache/index. Cách này phát hiện được ít nhất 2 lần AI báo cáo sai: 1 lần fix
Bug 3 thiếu ký tự  trong f-string khiến cache key không hoạt động dù báo
cáo ghi "16 passed", và 1 lần E2E test fail do quên rebuild Docker container
chứ không phải bug thật.

## Log các prompt chính đã dùng

### Bug 1 — JWT không kiểm tra hết hạn

> Trong file ackend/app/core/security.py, hàm erify_token() đang tắt
> việc kiểm tra hạn token bằng options={"verify_exp": False}... [Xóa
> option đó, thêm docstring giải thích exp được validate mặc định]
>
> Thêm test 	est_expired_access_token_rejected và
> 	est_valid_access_token_accepted vào 	est_auth.py, dùng
> create_access_token(data={"sub": ...}, expires_delta=timedelta(minutes=-5))
> để giả lập token hết hạn.

### Bug 2 — IDOR (đọc/sửa/xóa todo của user khác)

> Đổi signature get_todo_by_id() thêm tham số user_id, lọc đồng thời
> Todo.id == todo_id và Todo.user_id == user_id trong cùng 1 query...
> Dùng 404 (không phải 403) cho cả 2 trường hợp không tồn tại / không sở hữu.
>
> Viết 3 test 	est_cannot_{get,update,delete}_other_users_todo dùng 2 user
> A/B riêng biệt qua helper get_auth_token() có sẵn.

### Bug 3 + 4 — Cache rò rỉ giữa user & không invalidate

> Đổi cache_key = "todos:list" thành
> cache_key = f"todos:list:{current_user.id}:{page}:{size}"... Thêm method
> delete_pattern() dùng scan_iter vào RedisClient, gọi sau mỗi thao
> tác tạo/sửa/xóa todo... Thay mock Redis trong test (luôn trả None) bằng
> FakeRedis có state thật để test phản ánh đúng hành vi cache.

### Bug 5 + 6 — Toggle completed & partial update xóa field

> Đổi 	odo_data.model_dump() thành model_dump(exclude_unset=True), check
> bằng "completed" in update_data / "title" in update_data thay vì
> truthy check trên giá trị...

### Bug 7 — Refresh token dùng như access token

> Thêm check if payload.get("type") != "access": trong get_current_user()
> ngay sau khi verify payload...

### Bug 8 — Frontend logout không clear cache

> Thêm queryClient.clear() vào onSuccess của mutation logout trong
> useLogout()...

### Tier 2B — Playwright E2E

> Setup @playwright/test, viết 2 test: happy-path CRUD todo, và cross-user
> isolation dùng 2 rowser.newContext() độc lập thay vì login/logout cùng
> 1 tab...

### Tier 3B — Docker optimization

> Thêm .dockerignore cho backend/frontend, chuyển ackend/Dockerfile
> sang multi-stage build (builder stage cài gcc, runtime stage chỉ copy
> package đã cài)... Tạo docker-compose.prod.yml không hardcode secrets,
> dùng biến môi trường...

### Tier 3C — Database optimization

> Tạo Alembic migration thêm index ix_todos_user_id... Chạy EXPLAIN
> ANALYZE trước/sau bằng psql thật (không dùng số liệu giả định).

## Ghi chú

Đây là log tóm tắt các prompt chính, không phải transcript đầy đủ 100% từng
tin nhắn trao đổi (bao gồm cả các bước hỏi-đáp debug, xác nhận, sửa lỗi
nhỏ). Log chi tiết đầy đủ hơn có thể cung cấp nếu người chấm bài cần.
