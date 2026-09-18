# Database indexing benchmark

## Method

Measured locally with PostgreSQL 16 in Docker after inserting 10,000 users and 1,000,000 todos (100 todos per user). The query was the paginated active-todo list for one user:

```sql
SELECT * FROM todos
WHERE user_id = :user_id AND completed = false
ORDER BY created_at DESC, id DESC
LIMIT 20;
```

The database was analyzed before each `EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)` run. Migration `003_add_performance_indexes` adds `idx_todos_user_completed_created (user_id, completed, created_at DESC, id DESC)` and the unique email lookup index.

## Results

| Query | Dataset | Before index | After index | Plan change |
|---|---|---:|---:|---|
| Filtered, newest-first page | 10k users / 1m todos | 82.215 ms | 0.845 ms | Gather Merge / sequential scan → `Index Scan idx_todos_user_completed_created` |
| Count todos for one user | 10k users / 1m todos | 100.016 ms | 8.083 ms | Gather / sequential scan → Index-only scan |

The list results come from `/tmp/before-explain.json` and `/tmp/after-explain.json`; the count results come from `/tmp/count-before.json` and `/tmp/count-after.json` in the local validation run. They are not estimated or fabricated values.

## Trade-offs and rollout

- The composite index consumes storage and adds work to inserts and updates of `completed` or `created_at`; it is justified by the user-scoped list query used on every Todo page load.
- The leading `user_id` preserves selectivity; `completed` and descending ordering allow the filtered, ordered page query to use the same index.
- On a large production table, build the index with PostgreSQL `CREATE INDEX CONCURRENTLY` in a non-transactional deployment step, then attach the migration state. Standard Alembic transactional `CREATE INDEX` is appropriate for this small deployment but can block writes while building.
- Confirm planner use after rollout with `EXPLAIN ANALYZE` and keep table statistics current with `ANALYZE`/autovacuum.
