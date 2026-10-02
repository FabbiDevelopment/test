# Todo Index Benchmark

## Query and index

`GET /api/v1/todos` filters by `user_id`, paginates, and now orders by `created_at DESC, id DESC` for deterministic results. The count query filters by `user_id`. The Alembic migration adds a B-tree index on `(user_id, created_at, id)`. PostgreSQL can scan the matching index entries backward for the requested descending order; the leading `user_id` also supports the count filter.

The suggested `(user_id, completed, created_at)` index was not used because the current endpoint does not filter by `completed`. With `completed` between `user_id` and `created_at`, that index would not provide the requested ordering when only `user_id` is constrained.

## Measurement

Measured with `EXPLAIN (ANALYZE, BUFFERS)` against the project's existing PostgreSQL 16.14 database, using the same representative user and query before and after the migration. The database had 1,002 todos across 124 users; the selected user had 17 todos. This is a warm-cache, single-run measurement on the existing dataset, not a million-row load test.

| Query | Plan before | Before | Plan after | After |
|---|---|---:|---|---:|
| User-filtered page ordered by `created_at DESC, id DESC` (`LIMIT 20`) | Sequential scan + sort | 1.394 ms | Bitmap index scan + heap scan + sort | 0.117 ms |
| Count todos for one user | Sequential scan | 0.251 ms | Bitmap index scan + heap scan | 0.135 ms |

The page query still sorts the 17 matching rows on this small dataset. The benchmark confirms that filtering uses the new index, but a representative large-data benchmark is needed to assess whether PostgreSQL can avoid the sort and to generalize the latency change.

## Reproduction queries

Replace `'<user_uuid>'` with the same user UUID for both runs:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = '<user_uuid>'
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 0;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM todos
WHERE user_id = '<user_uuid>';
```

## Trade-offs and migration safety

- **Write latency:** Inserts maintain one additional B-tree entry; updates to indexed columns also update the index. This adds write I/O and CPU.
- **Storage:** The index stores each todo's user UUID, timestamps, and row reference. Measure its size with `pg_relation_size('ix_todos_user_created_at_id')` on production-like data.
- **Large-table migration:** The migration uses PostgreSQL `CREATE INDEX CONCURRENTLY` so normal writes are not blocked for the full build. It takes longer, consumes I/O and temporary disk space, and runs in Alembic's autocommit block because PostgreSQL disallows concurrent index creation inside a transaction. Monitor the build and available disk; if it fails, check for and remove an invalid index before retrying. Downgrade also drops the index concurrently.

## Dataset limitation

The existing project database already had todos. The seed script skips todo generation when any todo exists, so it was not run against this database. No existing rows were deleted or bulk-added for this benchmark.
