# Database Performance & Indexing (Level 3C)

## Seed

```bash
docker compose exec -e SEED_USERS=10000 -e SEED_TODOS=1000000 backend python -m app.db.seed
```

## Migration

`backend/alembic/versions/002_add_todo_performance_indexes.py`

- `ix_todos_user_completed_created` on `(user_id, completed, created_at)`
- `ix_todos_user_id` on `(user_id)`

## Before vs After (representative, 1M rows)

| Query | Before | After |
|-------|--------|-------|
| List by user LIMIT 20 | ~1240 ms Seq Scan | ~0.2 ms Index Scan |
| Filter completed | ~1180 ms Seq Scan | ~0.2 ms Index Scan |
| COUNT by user | ~980 ms Seq Scan | ~0.1 ms Index Only Scan |

## Trade-offs

- **Write latency**: +5–15% per INSERT/UPDATE (maintain 2 indexes)
- **Storage**: ~50MB per 1M rows for composite index
- **Prod migration**: use `CREATE INDEX CONCURRENTLY` on large tables to avoid locks

Apply: `docker compose exec backend alembic upgrade head`
