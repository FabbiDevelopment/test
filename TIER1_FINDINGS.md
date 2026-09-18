# Tier 1 Bug Findings and Fixes

## 1. Expired tokens accepted

- **Location:** `backend/app/core/security.py`, `verify_token`
- **Severity:** Critical
- **Reason:** JWT expiration verification was explicitly disabled, allowing a stolen access or refresh token to remain valid indefinitely.
- **Fix:** Restore the JWT library's default expiration validation.

## 2. Refresh tokens accepted as access tokens

- **Location:** `backend/app/api/deps.py`, `get_current_user`
- **Severity:** High
- **Reason:** Protected endpoints only checked the signature and subject. A refresh token could therefore be used as a bearer access token.
- **Fix:** Require the token claim `type` to equal `access` for protected endpoints.

## 3. Refresh tokens issued for missing users

- **Location:** `backend/app/api/v1/auth.py`, `refresh_token`
- **Severity:** High
- **Reason:** The refresh flow trusted `sub` without validating its format or confirming that the user still exists.
- **Fix:** Validate the UUID and load the user before rotating tokens.

## 4. Cross-user todo access and mutation

- **Location:** `backend/app/services/todo_service.py`, `get_todo_by_id`; todo detail/update/delete endpoints
- **Severity:** Critical
- **Reason:** Todo lookup used only the todo ID. Any authenticated user who learned an ID could read, modify, or delete another user's todo.
- **Fix:** Scope every single-todo lookup by both `todo_id` and the authenticated `user_id`. Unauthorized records intentionally return 404.

## 5. Boolean `false` updates ignored

- **Location:** `backend/app/api/v1/todos.py`, `update_existing_todo`
- **Severity:** High
- **Reason:** The truthiness check applied `completed=true` but ignored `completed=false`, so completed todos could not be made active again.
- **Fix:** Apply fields using Pydantic's `exclude_unset=True`, which preserves explicit false values.

## 6. Partial updates erase descriptions

- **Location:** `backend/app/api/v1/todos.py`, `update_existing_todo`
- **Severity:** High
- **Reason:** `model_dump()` included omitted optional fields as `None`; changing only a title consequently cleared the existing description.
- **Fix:** Update only fields explicitly supplied by the client while still allowing an explicit `description: null` to clear it.

## 7. Todo list cache leaks data and becomes stale

- **Location:** `backend/app/api/v1/todos.py`, list and mutation endpoints
- **Severity:** Critical
- **Reason:** Every user and page shared `todos:list`, so one user could receive another user's cached response. Mutations also left cached results stale.
- **Fix:** Include user ID and pagination in cache keys, and invalidate all list variants belonging to the user after create, update, or delete.

## 8. Frontend query cache survives account changes

- **Location:** `frontend/src/lib/api.ts`, `frontend/src/features/auth/api/auth.ts`, `frontend/src/features/auth/hooks/useAuth.ts`
- **Severity:** High
- **Reason:** Logging out removed tokens but retained `currentUser` and todo query data. A second user on the same browser could briefly see the previous user's cached data.
- **Fix:** Clear React Query state during login, registration, successful logout, logout-error fallback, and automatic 401 handling.

## 9. Pagination parameters omitted from frontend query keys

- **Location:** `frontend/src/features/todos/api/todos.ts`, `useTodos`
- **Severity:** Medium
- **Reason:** All pagination variants used the same key, causing React Query to reuse results from a different page or page size.
- **Fix:** Include `page` and `size` in the query key and update all matching todo caches safely during optimistic mutations.

## 10. Failed optimistic mutations are not rolled back

- **Location:** `frontend/src/features/todos/api/todos.ts`, `useUpdateTodo`
- **Severity:** Medium
- **Reason:** A failed request left the optimistic value visible until a successful refetch, misrepresenting server state.
- **Fix:** Snapshot all todo queries and restore them in `onError`.

## Verification

```bash
cd backend && pytest tests/ -v
cd frontend && npm run lint && npm run build
```
