# Database Performance & Indexing Strategy

> Task 3C. Toàn bộ số liệu trong tài liệu này chạy **thật** trên PostgreSQL
> 16 với dữ liệu seed **thật** theo đúng lệnh README:
> `SEED_USERS=10000 SEED_TODOS=1000000` → `python -m app.db.seed`, không
> phải số liệu ước lượng.

## 1. Môi trường benchmark

- PostgreSQL 16.15 (local, không phải Docker container do sandbox không có
  Docker daemon — dùng trực tiếp `postgresql-16` cài qua `apt`).
- Schema tạo bằng `alembic upgrade head` (đúng model hiện có trong repo).
- Dữ liệu: **10,000 users, 1,000,000 todos**, phân bố ngẫu nhiên
  (trung bình 100 todo/user, tối đa ~139 todo cho user đông nhất).
- User dùng để benchmark: 1 user có **139 todos** (đại diện mức trung bình
  trên-mức, để thấy rõ hiệu ứng `LIMIT`/`ORDER BY`/pagination).
- Trước khi thêm index mới, `todos` **chỉ có đúng 1 index**: PK trên `id`
  (`todos_pkey`) — không có bất kỳ index nào trên `user_id`, dù đây là điều
  kiện lọc ở **mọi** query hiện có trong `todo_service.py`.

## 2. Query được benchmark

Lấy trực tiếp từ các query app đang chạy (`app/services/todo_service.py`)
cộng với đúng 3 loại README yêu cầu:

| # | Query | Tương ứng với |
|---|---|---|
| Q1 | `SELECT * FROM todos WHERE user_id = :uid ORDER BY created_at DESC LIMIT 20` | `GET /todos` (danh sách phân trang) |
| Q2 | `SELECT count(*) FROM todos WHERE user_id = :uid` | `total` trong `TodoListResponse` |
| Q3 | `SELECT * FROM todos WHERE user_id = :uid AND completed = false ORDER BY created_at DESC LIMIT 20` | Filter "chỉ xem chưa hoàn thành" — pattern phổ biến, minh hoạ giá trị của composite index |

> **Lưu ý phát hiện thêm**: `get_todos()` hiện tại trong
> `todo_service.py` **không có `ORDER BY`** trong query thật (chỉ có
> `.offset().limit()`). Điều này là 1 bug tiềm ẩn khác (không thuộc phạm vi
> Task 3C nhưng đáng ghi nhận): pagination không có `ORDER BY` tường minh
> có thể trả về thứ tự không ổn định giữa các lần gọi, khiến user thấy
> trùng/thiếu item khi chuyển trang. Q1/Q3 ở trên dùng `ORDER BY created_at
> DESC` vì đó là hành vi **đúng** mà endpoint nên có — cũng là ví dụ README
> yêu cầu benchmark ("ordering by created_at").

## 3. EXPLAIN ANALYZE — Trước khi thêm index

Chỉ có `todos_pkey` (PK trên `id`). Mọi query đều rơi vào
**Parallel Seq Scan** quét toàn bộ 1 triệu dòng:

```
=== Q1: Paginated list, ordered by created_at DESC ===
 Limit  (cost=33148.47..33150.81 rows=20 width=185) (actual time=106.871..110.787 rows=20 loops=1)
   ->  Gather Merge  (Workers Launched: 2)
         ->  Sort (Sort Key: created_at DESC, Sort Method: top-N heapsort)
               ->  Parallel Seq Scan on todos
                     Filter: (user_id = '3f011a1e-...'::uuid)
                     Rows Removed by Filter: 333287
 Planning Time: 0.412 ms
 Execution Time: 110.827 ms

=== Q2: Count todos for user ===
 Finalize Aggregate (actual time=112.160..113.199 rows=1 loops=1)
   ->  Gather (Workers Launched: 2)
         ->  Partial Aggregate
               ->  Parallel Seq Scan on todos
                     Filter: (user_id = '3f011a1e-...'::uuid)
                     Rows Removed by Filter: 333287
 Execution Time: 113.273 ms

=== Q3: Filtered by completed=false, ordered, paginated ===
 Limit (actual time=121.444..121.498 rows=20 loops=1)
   ->  Gather Merge (Workers Launched: 2)
         ->  Sort (Sort Key: created_at DESC, Sort Method: quicksort)
               ->  Parallel Seq Scan on todos
                     Filter: ((NOT completed) AND (user_id = '3f011a1e-...'::uuid))
                     Rows Removed by Filter: 333311
 Execution Time: 121.538 ms
```

Cả 3 query đều phải **loại bỏ ~333,000 dòng không khớp** sau khi quét toàn
bảng, dù kết quả cuối chỉ cần 20-139 dòng — độ lệch giữa dữ liệu cần đọc và
dữ liệu thực sự dùng là ~99.99%.

## 4. Migration thêm index

`backend/alembic/versions/b3f7c9a21d44_add_todos_composite_index.py`:

```python
op.create_index(
    "ix_todos_user_id_completed_created_at",
    "todos",
    ["user_id", "completed", "created_at"],
    unique=False,
    postgresql_concurrently=True,
    if_not_exists=True,
)
```

**Vì sao thứ tự cột `(user_id, completed, created_at)`?**
- `user_id` đứng đầu vì **mọi** query đều lọc theo nó (equality) — đây là
  điều kiện chọn lọc nhất, giúp Postgres dùng B-tree để nhảy thẳng đến đúng
  nhóm dòng của 1 user thay vì quét toàn bảng.
- `completed` đứng thứ 2 (cũng equality trong Q3) — index B-tree cho phép
  "prefix match" nên `(user_id)` và `(user_id, completed)` đều tận dụng
  được index này, không cần index riêng cho từng combo.
- `created_at` đứng cuối vì dùng cho `ORDER BY` — khi 2 cột đầu đã cố định
  giá trị (qua `WHERE`), phần còn lại của mỗi "nhóm" trong B-tree đã **sẵn
  sàng có thứ tự theo `created_at`**, nên Postgres có thể trả kết quả đã
  sort mà **không cần thêm bước Sort riêng** (thấy rõ ở Q3 sau khi có index
  — `Index Scan Backward`, không còn node `Sort`).

Chạy bằng `CREATE INDEX CONCURRENTLY` (qua `autocommit_block()` của
Alembic) — xem mục 6 để biết lý do.

## 5. EXPLAIN ANALYZE — Sau khi thêm index

```
=== Q1: Paginated list, ordered by created_at DESC ===
 Limit (actual time=1.046..1.050 rows=20 loops=1)
   ->  Sort (Sort Key: created_at DESC, top-N heapsort)
         ->  Bitmap Heap Scan on todos (actual time=0.052..0.943 rows=139)
               Recheck Cond: (user_id = '3f011a1e-...'::uuid)
               ->  Bitmap Index Scan on ix_todos_user_id_completed_created_at
                     Index Cond: (user_id = '3f011a1e-...'::uuid)
 Execution Time: 1.090 ms

=== Q2: Count todos for user ===
 Aggregate (actual time=0.058..0.058 rows=1 loops=1)
   ->  Index Only Scan using ix_todos_user_id_completed_created_at on todos
         Index Cond: (user_id = '3f011a1e-...'::uuid)
         Heap Fetches: 0
 Execution Time: 0.106 ms

=== Q3: Filtered by completed=false, ordered, paginated ===
 Limit (actual time=0.023..0.103 rows=20 loops=1)
   ->  Index Scan Backward using ix_todos_user_id_completed_created_at on todos
         Index Cond: ((user_id = '3f011a1e-...'::uuid) AND (completed = false))
 Execution Time: 0.126 ms
```

Q2 trở thành **Index Only Scan** với `Heap Fetches: 0` — Postgres trả lời
được hoàn toàn từ index, không cần chạm vào bảng dữ liệu chính. Q3 loại bỏ
hẳn node `Sort` vì index đã có sẵn thứ tự đúng.

## 6. Bảng Benchmark: Before vs After

| Query | Before (Seq Scan) | After (Index Scan) | Speedup | Query Plan thay đổi |
|---|---|---|---|---|
| Q1 — Paginated list, `ORDER BY created_at` | **110.83 ms** | **1.09 ms** | **~102×** | Parallel Seq Scan + Sort → Bitmap Index Scan + top-N heapsort (nhỏ hơn nhiều) |
| Q2 — `COUNT(*) WHERE user_id` | **113.27 ms** | **0.11 ms** | **~1068×** | Parallel Seq Scan → **Index Only Scan** (0 heap fetch) |
| Q3 — Filter `completed=false` + order | **121.54 ms** | **0.13 ms** | **~964×** | Parallel Seq Scan + Sort → Index Scan Backward (**không còn Sort**) |

*(Môi trường: 1 kết nối, không cache warm-up đặc biệt giữa các lần chạy —
số liệu "before" và "after" đều lấy từ lần `EXPLAIN ANALYZE` đầu tiên sau
`ANALYZE` để phản ánh đúng chi phí thực tế, không phải best-case sau khi
buffer cache đã "nóng" từ query trước.)*

### Bảng đo write-latency (chi phí ghi thêm do index)

Đo trực tiếp bằng `INSERT ... SELECT ... FROM generate_series(1, 20000)`
(bulk insert 20,000 dòng), so sánh có/không có index, trên cùng 1 bảng đã
có 1,000,000 dòng sẵn:

| | Không có index | Có index `(user_id, completed, created_at)` | Chênh lệch |
|---|---|---|---|
| 20,000 INSERT (bulk) | 193.3 ms | 560.8 ms | **+190%** (chậm hơn ~2.9×) |
| Trung bình / 1 INSERT | ~0.0097 ms | ~0.028 ms | +0.018 ms/row |

## 7. Index Tradeoffs

- **Write latency**: mỗi INSERT giờ phải ghi thêm 1 entry vào B-tree index
  (ngoài heap + PK index), đo được **chậm hơn ~2.9×** ở benchmark bulk
  insert. Về số tuyệt đối, +0.018ms/row là **không đáng kể** so với chi phí
  round-trip mạng + ORM overhead của 1 API request thực tế (thường vài ms
  trở lên) — đánh đổi này hoàn toàn hợp lý cho 1 bảng có tỷ lệ đọc/ghi
  nghiêng hẳn về đọc (todo list được đọc mỗi lần mở app, chỉ ghi khi
  tạo/sửa/xoá 1 todo).
- **Storage overhead**: index mới chiếm **48 MB**, so với **210 MB** dữ
  liệu bảng (~23% overhead) trên tập 1.04 triệu dòng — chấp nhận được, và
  sẽ scale tuyến tính theo số dòng, không phải theo cấp số nhân.
- **Migration safety trên bảng lớn ở production**:
  - Dùng `CREATE INDEX CONCURRENTLY` (đã áp dụng trong migration) thay vì
    `CREATE INDEX` thường — tránh giữ `ACCESS EXCLUSIVE` lock chặn toàn bộ
    INSERT/UPDATE/DELETE trên `todos` trong suốt quá trình build index (có
    thể mất hàng phút trên bảng hàng triệu dòng). `CONCURRENTLY` chỉ giữ
    lock nhẹ, cho phép ghi bình thường song song, đổi lại build lâu hơn
    (~2-3× so với build thường) và **không thể chạy trong 1 transaction**
    (Alembic xử lý qua `autocommit_block()`).
  - Rủi ro cần biết: nếu `CREATE INDEX CONCURRENTLY` bị fail/interrupt
    giữa chừng, nó để lại 1 **index "invalid"** thay vì tự rollback sạch —
    cần `DROP INDEX` thủ công rồi chạy lại, không tự động retry.
  - Benchmark thật trên máy hiện tại: build index trên 1,000,000 dòng mất
    **~2.4 giây** — ở production với I/O chậm hơn/bảng lớn hơn nhiều
    (chục triệu dòng), nên chạy migration này **ngoài giờ cao điểm** và
    theo dõi `pg_stat_progress_create_index` trong lúc chạy.
