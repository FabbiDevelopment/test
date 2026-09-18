# Bug Report and Fix Summary

| Severity | Location | Problem | Resolution |
|---|---|---|---|
| Critical | `backend/app/core/security.py` | JWT access tokens were decoded with expiration verification disabled. | Enforce normal JWT expiry validation and add a regression test. |
| Critical | `backend/app/api/deps.py` | A refresh token could be accepted by an access-token-only dependency. | Require token type `access` for protected endpoints and test it. |
| Critical | `backend/app/api/v1/todos.py`, `backend/app/services/todo_service.py` | A signed-in user could access another user's Todo by UUID. | Scope read, update, and delete lookups to the current owner and return `404` for foreign records. |
| High | `backend/app/api/v1/todos.py` | Partial Todo updates could overwrite omitted fields, including a description. | Serialize only fields explicitly supplied by the request. |
| High | `backend/app/api/v1/todos.py` | Setting `completed` from true to false was ignored by truthiness checking. | Distinguish `false` from an omitted value. |
| High | `backend/app/services/todo_service.py` | Todo listing had no deterministic sort order. | Order by `created_at DESC, id DESC` and add a supporting composite index. |
| High | `backend/app/api/v1/todos.py` and Redis cache | List cache could remain stale after mutations. | Invalidate every cached page for the affected user after create, update, or delete. |
| Medium | `frontend/src/features/todos/api/todos.ts` | Cached Todo data could cross logout/login boundaries or fail to roll back after a failed mutation. | Scope query keys by access token, clear cache on logout/401, and restore mutation snapshots on error. |
| Medium | `frontend/src/features/todos/components/TodoList.tsx` | Index-based React keys could render the wrong Todo after reordering. | Use the stable Todo UUID as the key. |

Validation is recorded in the manual plan, backend test suite, and Playwright E2E suite.
