# Todo Query Index Benchmark

## Objective

Measure the primary todo access patterns on PostgreSQL before and after adding workload-specific composite indexes:

1. A user's newest todos: `WHERE user_id = ? ORDER BY created_at DESC, id DESC LIMIT 20`.
2. A user's total todo count: `WHERE user_id = ?`.
3. A user's incomplete newest todos: `WHERE user_id = ? AND completed = false ORDER BY created_at DESC, id DESC LIMIT 20`.

## Dataset and method

- PostgreSQL: 16.15 (Homebrew), Apple Silicon.
- Dataset target: 10,000 users and 1,000,000 todos from `app.db.seed`.
- Representative input: the user with the highest todo count, selected once before both phases.
- Each phase runs `ANALYZE todos` and records `EXPLAIN (ANALYZE, BUFFERS, WAL)`.
- Script: `backend/scripts/benchmark_todo_queries.sql`.
- Results are wall-clock execution time reported by PostgreSQL, not client/network latency.

Commands:

```bash
docker compose exec -e SEED_USERS=10000 -e SEED_TODOS=1000000 backend python -m app.db.seed
docker compose exec postgres psql -U fabbi -d postgres -f /path/to/benchmark_todo_queries.sql
```

For a local PostgreSQL instance:

```bash
cd backend
DATABASE_URL=postgresql+asyncpg://fabbi:fabbi_secret@localhost:5432/postgres alembic downgrade a0790c76a129
DATABASE_URL=postgresql+asyncpg://fabbi:fabbi_secret@localhost:5432/postgres \
  SEED_USERS=10000 SEED_TODOS=1000000 python -m app.db.seed
psql postgresql://fabbi:fabbi_secret@localhost:5432/postgres \
  -f scripts/benchmark_todo_queries.sql
```

## Results

The table is populated only from captured PostgreSQL output. It must not be replaced with estimated timings.

| Query | Before | After | Change | Before plan | After plan |
|---|---:|---:|---:|---|---|
| User list, newest 20 | 41.154 ms | 0.053 ms | 99.87% lower (776x) | Parallel seq scan + top-N sort | Ordered index scan on `ix_todos_user_created_id` |
| User todo count | 41.295 ms | 0.401 ms | 99.03% lower (103x) | Parallel seq scan | Bitmap index + heap scan |
| Incomplete list, newest 20 | 43.872 ms | 0.020 ms | 99.95% lower (2,194x) | Parallel seq scan + sort | Ordered index scan on `ix_todos_user_completed_created_id` |

Captured dataset: 10,000 users, 1,000,000 todos. The representative user had 138 todos. The heap table was 212 MB; `ix_todos_user_created_id` was 56 MB and `ix_todos_user_completed_created_id` was 65 MB (121 MB combined).

These are local single-run results, not an SLA. The before phase read heap pages from disk while index creation and `ANALYZE` warmed part of the working set, so the measured ratio includes cache-state effects. The plan change and buffer reduction are the durable conclusions: the list query went from 27,307 shared buffers and a million-row scan to 23 buffers; the completed query likewise used 23 buffers. Production validation should use repeated cold/warm runs on representative hardware.

## Index design

### `ix_todos_user_created_id`

```sql
CREATE INDEX ON todos (user_id, created_at DESC, id DESC);
```

- Equality on `user_id` is first.
- The remaining columns match the deterministic sort, allowing an ordered index scan that stops after 20 rows.
- The `user_id` prefix also supports the count query and may allow an index-only scan after vacuum updates the visibility map.

### `ix_todos_user_completed_created_id`

```sql
CREATE INDEX ON todos (user_id, completed, created_at DESC, id DESC);
```

- Equality filters precede ordering columns.
- It avoids filtering the user's opposite-status rows and avoids an explicit sort.
- It does not replace the first index: placing `completed` between `user_id` and `created_at` cannot satisfy the unfiltered ordering across both boolean values.

## Trade-offs

- **Write latency:** every insert and updates to `user_id`, `completed`, `created_at`, or `id` maintain one or both B-trees. Todo creation and status toggles become more expensive.
- **Storage:** on this 1,000,000-row dataset, the 212 MB heap gained 121 MB of indexes (56 MB + 65 MB), about 57% of heap size before considering other indexes. Storage grows with row count.
- **Cache pressure:** additional indexes compete with table pages and other indexes in shared buffers.
- **Count complexity:** the index improves row location but exact counts remain O(rows for that user). At much larger per-user cardinality, consider approximate/counter designs with explicit consistency trade-offs.
- **Redundancy:** keep both only while both unfiltered and status-filtered workloads are product requirements and measured usage justifies them. Monitor `pg_stat_user_indexes`.

## Production migration safety

- Migration uses `CREATE INDEX CONCURRENTLY` inside Alembic autocommit blocks, so normal reads/writes are not blocked for the entire table scan.
- Concurrent builds take longer, consume I/O/CPU, and briefly take stronger locks at start/end; schedule and monitor them.
- PostgreSQL concurrent index creation cannot run inside a transaction. A failure may leave an `INVALID` index; runbook must detect it in `pg_index`, drop it concurrently, and retry.
- Deploy indexes before query changes, verify query plans/stats, then deploy consumers. Downgrade drops indexes concurrently.
- Ensure disk headroom for the table, completed indexes, and temporary build space; test on a production-sized clone.
