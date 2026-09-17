# Full-Stack Assessment Report

## Tier 1 Findings and Fixes

| Location | Severity | Reason | Fix |
|---|---|---|---|
| `backend/app/core/security.py`, `verify_token` | Critical | `verify_exp=False` accepted expired access tokens | Restore standard JWT expiration validation |
| `backend/app/api/deps.py`, `get_current_user` | Critical | Refresh tokens were accepted by protected endpoints | Require `payload.type == access` |
| `backend/app/api/v1/todos.py`, single-todo routes | Critical | User A could read, edit, or delete User B's todo by ID | Scope service query by `todo_id` and `current_user.id` |
| `backend/app/api/v1/todos.py`, list cache | Critical | One global Redis key leaked data and mixed pages/users | Scope key by user/page/size and invalidate user keys |
| `backend/app/api/v1/todos.py`, update | High | Truthy check prevented `completed=true` to `false` | Use `model_dump(exclude_unset=True)` |
| `frontend/src/features/todos/api/todos.ts` | High | Shared `['todos']` cache and incomplete rollback | Scope query by user/page/size and restore snapshots on error |
| `frontend/src/features/auth/api/auth.ts`, logout | High | React Query retained previous user's data after logout | Clear QueryClient on logout and 401 |
| `backend/app/models/user.py` and Alembic | High | Email uniqueness was application-only and race-prone | Add unique DB index and model metadata |

## Validation

- `docker compose run --rm --build backend pytest tests/ -v`: 14 passed.
- Frontend build stage completed Vite build and `npm run lint` successfully. The runtime image intentionally has no `package.json`, so `npm run lint` must run in the named build stage.
- `cd e2e; npm test`: 2 passed (full journey and cross-user isolation).
- Rebuilt Docker stack started with PostgreSQL and Redis healthy.

## Database Benchmark

Run these commands against the same database and representative dataset before and after migration `b2c3d4e5f6a7`:

```sql
EXPLAIN (ANALYZE, BUFFERS)
SELECT id, title, description, completed, user_id, created_at, updated_at
FROM todos
WHERE user_id = '00000000-0000-0000-0000-000000000001'
ORDER BY created_at DESC, id DESC
LIMIT 20 OFFSET 0;

EXPLAIN (ANALYZE, BUFFERS)
SELECT count(*) FROM todos
WHERE user_id = '00000000-0000-0000-0000-000000000001';
```

| Query | Before index | After index | Plan expectation |
|---|---:|---:|---|
| User list + ordering | 0.135 ms, sequential scan + sort | 0.050 ms, backward index scan | `ix_todos_user_created_id` satisfies owner filter and ordering |
| User count | 0.135 ms, sequential scan | 0.124 ms, index-only scan | Index plan avoids the table scan; timing is noise-level on an empty database |

Measured against the current Docker PostgreSQL database, which has no representative million-row dataset. These timings demonstrate plan changes, not a production capacity claim. Repeat with the seed command before using them for capacity planning.

Do not claim a timing without recording the actual `Execution Time` output. The composite index improves reads but adds write work and storage. On large production tables, review duplicates first and use a concurrent index migration where operational policy permits; concurrent creation cannot run inside the normal Alembic transaction.

## Commands

- Backend: `docker compose run --rm --build backend pytest tests/ -v`
- E2E: `cd e2e; npm install; npx playwright install; npx playwright test` or `npx playwright test --headed`
- Compose validation: `docker compose config`
- Production compose validation: `docker compose -f docker-compose.prod.yml config`
