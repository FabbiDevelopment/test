# Database Performance and Indexing

## Indexed queries

The Todo list query filters by `user_id`, orders by `created_at` and `id`, and
uses pagination. The count query filters by `user_id`. The authentication query
looks up a user by `email`.

Indexes:

- `users.email`: unique B-tree index `ix_users_email`.
- `todos(user_id, created_at)`: B-tree index `ix_todos_user_created_at`.
- Primary keys already index `users.id` and `todos.id`.

The composite Todo index also supports the `user_id` prefix used by the count
query. `completed`, `updated_at` and `title` are not indexed because current
production queries do not filter or order by those fields.

## EXPLAIN ANALYZE commands

Run these commands against a representative dataset after applying migrations:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = '<user-uuid>'
ORDER BY created_at DESC, id DESC
LIMIT 100 OFFSET 0;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*)
FROM todos
WHERE user_id = '<user-uuid>';

EXPLAIN (ANALYZE, BUFFERS)
SELECT id, email
FROM users
WHERE email = 'user@example.com';
```

Use the seed dataset described in `GUIDE.md` before comparing plans:

```bash
docker compose exec -e SEED_USERS=10000 -e SEED_TODOS=1000000 \
  backend python -m app.db.seed
```

## Before/after benchmark

The repository does not include a production-sized PostgreSQL dataset or a
repeatable benchmark runner, so runtime values must be recorded from the
target environment rather than invented. Capture `Execution Time`, planning
time, and whether the plan uses an Index Scan/Bitmap Index Scan.

| Query | Before | After | Expected plan change |
|---|---:|---:|---|
| User lookup by email | Record with no `ix_users_email` | Record after migration | Sequential Scan -> Index Scan |
| Todo list by user | Record with no Todo index | Record after migration | Sequential Scan/Sort -> Index Scan |
| Todo count by user | Record with no Todo index | Record after migration | Full scan -> Bitmap/Index Scan |

## Trade-offs and migration safety

- Indexes consume disk and memory.
- INSERT, UPDATE and DELETE must maintain the new indexes, adding write cost.
- The unique email index enforces a correctness rule as well as improving lookup.
- The composite Todo index supports both filtering and ordered pagination.
- On large production tables, create indexes using an online/concurrent
  deployment strategy where supported, and monitor locks, disk usage and
  replication lag.
