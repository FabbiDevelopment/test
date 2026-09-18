# Database Performance and Indexing

## Workload and Environment

Benchmark date: 2026-09-18.

- PostgreSQL 16 Alpine running in Docker Desktop.
- 1,000,006 todo rows during measurement.
- 1,000,000 marked benchmark rows belonged to `demo@test.com`.
- Each query was executed once as a warm-up before the recorded `EXPLAIN (ANALYZE, BUFFERS)`.
- Benchmark rows were deleted afterward and `VACUUM (FULL, ANALYZE)` restored the development table.

The production list query filters by `user_id`, orders by `created_at DESC, id DESC`, and applies a limit. The count query filters by `user_id`.

## Reproduction

Generate a representative data set:

```sql
INSERT INTO todos (
  id, title, description, completed, user_id, created_at, updated_at
)
SELECT
  gen_random_uuid(),
  'BENCHMARK_TODO_' || g,
  'generated for explain analyze',
  (g % 2 = 0),
  (SELECT id FROM users WHERE email = 'demo@test.com'),
  now() - (g * interval '1 millisecond'),
  now()
FROM generate_series(1, 1000000) AS g;

ANALYZE todos;
```

Measure the two core queries:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, completed, created_at
FROM todos
WHERE user_id = (
  SELECT id FROM users WHERE email = 'demo@test.com'
)
ORDER BY created_at DESC, id DESC
LIMIT 100;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM todos
WHERE user_id = (
  SELECT id FROM users WHERE email = 'demo@test.com'
);
```

## Results

| Query | Before index | After index | Change |
|---|---:|---:|---|
| Todo page, limit 100 | 68.944 ms | 0.068 ms | About 1,014x faster |
| Count all todos for benchmark user | 47.893 ms | 57.731 ms | About 20.5% slower |

Before indexing, the page query used a `Parallel Seq Scan`, scanned roughly one million rows, and performed a top-N sort. After indexing, it used `Index Scan Backward using ix_todos_user_created_id`, touched seven shared buffers, and returned 100 rows without a separate sort.

The count query changed from a parallel sequential scan to a parallel index-only scan with zero heap fetches. It was slower in this deliberately low-selectivity case because the selected user owned almost every row. This index is justified by the latency-sensitive paginated list, not by the full-user count alone.

At one million rows:

- Composite index size: 56 MB.
- Total `todos` relation size including indexes: 222 MB.

## Migration

Alembic migration `002_add_query_indexes` adds:

```sql
CREATE INDEX ix_todos_user_created_id
ON todos (user_id, created_at, id);
```

The key order matches equality filtering by user followed by descending traversal of creation time and ID. PostgreSQL can scan a B-tree backward, so explicit `DESC` index columns are unnecessary for this query.

The migration also adds a unique email index to enforce registration integrity at the database boundary.

## Tradeoffs and Production Safety

The index consumes storage and adds maintenance cost to every todo insert, delete, and update touching indexed columns. A broad count for a user owning most of the table may not improve and can regress slightly, as this benchmark demonstrates.

The index intentionally omits `completed` because the current production query does not filter by status. If status filtering is added, benchmark a separate `(user_id, completed, created_at, id)` index against real workload statistics before adding it.

For a large production table, create the index concurrently in a dedicated non-transactional Alembic migration to avoid a long write lock. Confirm disk headroom, monitor replication lag, and run `ANALYZE` after the build.
