# Assessment submission notes

## Meaningful issues corrected

| Location | Severity | Issue | Fix |
|---|---|---|---|
| `backend/app/core/security.py` — `verify_token` | Critical | Expired or malformed JWTs could bypass incomplete validation; refresh tokens were accepted by protected endpoints. | Require expiry and subject, validate signature/expiry, and require an access-token type for protected routes. |
| `backend/app/api/v1/todos.py` — `owned_todo` | Critical | A user could act on another user's todo if ownership was not enforced consistently. | Check ownership for read, update, and delete; scope every list query and cache key to the current user. |
| `backend/app/services/todo_service.py` — `update_todo` | High | Partial updates could overwrite omitted fields, including `completed: false`. | Use `exclude_unset=True` and apply supplied values, including false. |
| `backend/app/api/v1/todos.py` — `invalidate_user_cache` | High | Cached todo lists could stay stale after writes. | Delete the user's filtered list keys after create, update, delete, tag, and bulk changes. |
| `frontend/src/features/auth/api/auth.ts` — `useLogout` | Medium | Logout could leave another user's React Query data visible in the same tab. | Clear the query cache and both stored tokens on logout. |
| `backend/app/models/tag.py` — `uq_tags_user_name_ci` | Medium | Tags lacked a user-scoped, case-insensitive uniqueness guarantee. | Add the functional unique index and tag ownership checks. |

## Validation

- `pytest` covers expired/tampered tokens, cross-user read/update/delete, false toggles, partial updates, and cache invalidation.
- Playwright contains the required full user journey and cross-user isolation scenarios.
- `npm run build` and `npm run lint` pass.

```bash
docker compose up --build
docker compose exec backend python -m app.db.seed
(cd backend && pytest tests/ -v)
(cd e2e && npm ci && npx playwright install chromium && npx playwright test)
(cd frontend && npm run build && npm run lint)
```

The benchmark trade-offs and rollout safety are documented in `docs/DB_INDEXING_BENCHMARK.md`. AI-assistance disclosure and the available prompt log are in `docs/AI_ASSISTANCE.md`.
