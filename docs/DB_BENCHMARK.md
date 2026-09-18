# Todo Query Benchmark and Index Strategy

## Queries

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, completed, created_at
FROM todos
WHERE user_id = '<user_uuid>'
ORDER BY created_at DESC, id DESC
LIMIT 20;

EXPLAIN (ANALYZE, BUFFERS)
SELECT COUNT(*) FROM todos WHERE user_id = '<user_uuid>';
```

## Migration

Migration `b1a2c3d4e5f6_add_todo_query_indexes.py` adds:

- `ix_todos_user_created_id (user_id, created_at, id)` for the primary paginated list query.
- `ix_todos_user_completed_created (user_id, completed, created_at)` for future status-filtered list queries.
- `uq_users_email` to guarantee one account per email at the database layer.

## Measurement

The measurement used an isolated `fabbi_benchmark` PostgreSQL database, so application data in `postgres` was untouched. The seed job completed **715,000 Todos across 10,000 users** before the command time limit; this remains a large, selectively queried dataset. The tested user owned 129 Todos.

Each query used `EXPLAIN (ANALYZE, BUFFERS, TIMING OFF)` three times. The table reports the median `Execution Time` on the local Docker environment.

| Query | Before | After | Improvement | Plan change |
|---|---:|---:|---|
| User list ordered by creation time, `LIMIT 20` | 34.558 ms | 0.056 ms | 617× faster | Parallel sequential scan + sort → `ix_todos_user_created_id` index scan |
| Count todos by user | 37.896 ms | 0.058 ms | 653× faster | Parallel sequential scan → index-only scan on `ix_todos_user_completed_created` |

To reproduce on a fresh database, apply migrations only through `a0790c76a129`, seed with `SEED_USERS` and `SEED_TODOS`, measure, upgrade to `head`, run `ANALYZE todos`, then repeat the same SQL and user ID. Execution times will vary by host, cache warmth, and PostgreSQL configuration.

## Tradeoffs and migration safety

Indexes increase disk use and make inserts/updates slower because PostgreSQL maintains each index. On large production tables, create indexes concurrently in a separately managed migration, monitor lock time and disk capacity, and schedule during a low-write window. Do not claim timing results from a dataset other than the measured one.
