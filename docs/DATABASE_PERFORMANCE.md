# Database Performance and Indexing Strategy

## 1. Objective

Tối ưu các query cốt lõi của Todo list khi bảng `todos` tăng đến 1.000.000 rows:

1. Lấy Todo theo `user_id`.
2. Lấy Todo theo user và sắp xếp mới nhất trước.
3. Đếm tổng Todo của user để phân trang.

## 2. Benchmark environment

- Database: PostgreSQL 16 Alpine chạy trong Docker Desktop.
- Dataset: 10.000 users và 1.000.000 todos từ `app.db.seed`.
- Database benchmark: `todo_benchmark_codex`, tách biệt với database ứng dụng.
- Sample user: có 138 todos.
- Statistics được cập nhật bằng `ANALYZE todos` trước khi đo.
- Cả baseline và indexed run đều được warm trước khi ghi nhận số liệu.
- Thời gian trong bảng là `Execution Time` từ `EXPLAIN (ANALYZE, BUFFERS)`; không bao gồm network hoặc JSON serialization.

Seed command:

```bash
docker compose exec \
  -e SEED_USERS=10000 \
  -e SEED_TODOS=1000000 \
  backend python -m app.db.seed
```

## 3. Queries under test

### Q1 — Fetch by user

```sql
SELECT id, title, completed, created_at
FROM todos
WHERE user_id = :user_id
LIMIT 20;
```

### Q2 — Fetch and order by creation time

```sql
SELECT id, title, completed, created_at
FROM todos
WHERE user_id = :user_id
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

`id DESC` là tie-breaker để thứ tự ổn định khi nhiều Todo có cùng `created_at`, đồng thời phù hợp với cursor pagination trong tương lai.

### Q3 — Count by user

```sql
SELECT count(*)
FROM todos
WHERE user_id = :user_id;
```

Mỗi query được đo bằng:

```sql
EXPLAIN (ANALYZE, BUFFERS) <query>;
```

## 4. Baseline findings

Không có index bắt đầu bằng `user_id`, PostgreSQL phải dùng Parallel Sequential Scan:

- Q1 loại bỏ hàng trăm nghìn rows trước khi tìm đủ 20 kết quả.
- Q2 scan toàn bộ 1.000.000 rows, sau đó `top-N heapsort` theo `created_at, id`.
- Q3 scan toàn bộ bảng bằng ba worker rồi aggregate.

Plan summary:

| Query | Baseline plan | Buffers | Execution time |
|---|---|---:|---:|
| Q1 — Fetch by user | Parallel Seq Scan | 10.356 | 21,445 ms |
| Q2 — Fetch + sort | Parallel Seq Scan → top-N Sort | 27.091 | 42,454 ms |
| Q3 — Count | Parallel Seq Scan → Aggregate | 26.961 | 43,788 ms |

## 5. Index design

Selected index:

```sql
CREATE INDEX CONCURRENTLY ix_todos_user_created_at_id
ON todos (user_id, created_at DESC, id DESC);
```

Rationale:

- `user_id` đứng đầu vì mọi query cốt lõi đều giới hạn theo owner.
- `created_at DESC, id DESC` khớp hoàn toàn với thứ tự list, loại bỏ bước sort.
- Q3 có thể dùng Index Only Scan vì `user_id` có trong index.
- Index vẫn phục vụ Q1 dù query không yêu cầu ordering.

Không đặt `completed` giữa `user_id` và `created_at`: API hiện tại chưa filter theo completed. Với query lấy tất cả trạng thái, index `(user_id, completed, created_at)` không thể cung cấp global ordering theo `created_at` vì các row bị chia thành hai nhóm completed. Nếu thêm status filter trong tương lai, cần benchmark một index riêng hoặc partial indexes dựa trên traffic thực tế.

Application query cũng được chuẩn hóa thành:

```sql
ORDER BY created_at DESC, id DESC
```

để kết quả phân trang có thứ tự xác định và sử dụng đúng index.

## 6. Benchmark results

| Query | Before | After | Speed-up |
|---|---:|---:|---:|
| Q1 — Fetch todos by user | 21,445 ms | 0,259 ms | 82,8× |
| Q2 — Fetch and sort | 42,454 ms | 0,056 ms | 758,1× |
| Q3 — Count todos | 43,788 ms | 0,207 ms | 211,5× |

Post-index plans:

- Q1: `Index Scan`, 23 shared buffer hits.
- Q2: `Index Scan`, 23 shared buffer hits và không còn Sort node.
- Q3: `Index Only Scan`, 45 shared buffer hits.
- Index size trên 1.000.000 rows: **56 MB**.

Kết quả phụ thuộc phần cứng, cache state, PostgreSQL configuration và phân bố dữ liệu. Các con số trên là phép đo của môi trường local, không phải production SLA.

## 7. Alembic migration

Migration `b94c6f2a10e1_add_todo_lookup_index.py` tạo và xóa index bằng `CONCURRENTLY` trong `autocommit_block`:

```bash
cd backend
alembic upgrade head
```

Validation:

```sql
SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'todos';
```

## 8. Trade-offs

### Write latency

Mọi `INSERT`, thay đổi `user_id`, `created_at` hoặc `id` phải duy trì thêm B-tree. Create Todo sẽ tốn thêm CPU và I/O; update chỉ thay đổi title/description/completed thường không đổi index này, nhưng vẫn có thể chịu thêm vacuum/storage pressure.

### Storage

Index chiếm 56 MB với dataset benchmark 1.000.000 rows. Kích thước tăng theo số Todo và có thể bloat khi write/delete nhiều. Theo dõi `pg_relation_size`, dead tuples và autovacuum; chỉ `REINDEX CONCURRENTLY` khi số liệu vận hành chứng minh cần thiết.

### Count behavior

Index Only Scan nhanh nhất khi visibility map được vacuum tốt. Benchmark vẫn có 40 heap fetches; autovacuum/VACUUM có thể giảm con số này. PostgreSQL vẫn phải đếm mọi index entry khớp user, vì vậy user có hàng triệu Todo có thể cần counter table hoặc approximate count ở giai đoạn sau.

### Large-table migration safety

- `CREATE INDEX CONCURRENTLY` tránh khóa write dài, nhưng chạy chậm hơn và thực hiện nhiều lượt scan.
- Migration cần thêm disk headroom cho index, WAL và replication lag.
- Không chạy trong transaction; failure có thể để lại invalid index. Trước khi retry, kiểm tra `pg_index.indisvalid` và drop invalid index bằng `DROP INDEX CONCURRENTLY`.
- Chỉ chạy một concurrent index build cho bảng này tại một thời điểm và theo dõi CPU, I/O, locks cùng replica lag.
- Deploy query ordering sau hoặc cùng thời điểm index đã valid; rollback application không yêu cầu drop index ngay.

## 9. Production verification checklist

1. Kiểm tra đủ disk headroom trên primary và replicas.
2. Chạy migration trong maintenance window có giám sát.
3. Xác nhận index `indisvalid = true`.
4. Chạy `ANALYZE todos` nếu statistics chưa được cập nhật.
5. Chạy lại ba `EXPLAIN (ANALYZE, BUFFERS)` bằng user đại diện.
6. Theo dõi p95 list latency, write latency, WAL volume và replication lag.
7. Giữ index nếu read benefit vượt write/storage cost; không thêm index `completed` khi chưa có query cần nó.
