# Frontend and Backend Code Review Findings

Date: 2026-06-06

This review used two read-only subagents: one focused on backend behavior and one focused on frontend behavior. No code changes were made during the review.

## Functional Bugs

### 1. Critical backend: expired JWTs are accepted indefinitely

Evidence: `backend/app/core/security.py:56` decodes JWTs with `options={"verify_exp": False}`. Both protected endpoints through `backend/app/api/deps.py:20` and token refresh through `backend/app/api/v1/auth.py:84` rely on this verifier.

Why this is a bug: access and refresh token expiration settings are effectively ignored. Old or stolen tokens remain valid forever.

Fix direction: remove `verify_exp: False`, let JWT decoding enforce expiration, and add tests for expired access and refresh tokens.

### 2. High backend: refresh tokens can access protected API routes

Evidence: refresh tokens are minted with `type: "refresh"` in `backend/app/core/security.py:42`, but `backend/app/api/deps.py:20` only validates the token subject and does not require `type == "access"`.

Why this is a bug: a refresh token can be used as a bearer token for `/auth/me` and todo CRUD endpoints, defeating the access/refresh token separation.

Fix direction: require `payload.get("type") == "access"` in `get_current_user`; keep refresh-token validation only in `/auth/refresh`.

### 3. High backend: users can read, update, and delete other users' todos by UUID

Evidence: single todo fetch/update/delete routes call `get_todo_by_id(db, todo_id)` in `backend/app/api/v1/todos.py:95`, `backend/app/api/v1/todos.py:114`, and `backend/app/api/v1/todos.py:145`. The service query filters only by todo id in `backend/app/services/todo_service.py:42`.

Why this is a bug: possession of another todo UUID is enough to access or mutate it. Ownership is enforced for list queries, but not item-level routes.

Fix direction: fetch todos by both `todo_id` and `current_user.id`, or explicitly compare `todo.user_id` before returning, updating, or deleting.

### 4. High backend: Redis todo list cache leaks data across users and pages

Evidence: `backend/app/api/v1/todos.py:37` uses one cache key, `todos:list`, and returns cached data before querying by `current_user.id`. It stores user-filtered and page-specific responses under the same key at `backend/app/api/v1/todos.py:72`.

Why this is a bug: one user or page request can receive another user's cached todo list, including `user_id` and `user_email`. Pagination responses can also be wrong.

Fix direction: include user id, page, size, and any filters in the cache key, for example `todos:list:{user_id}:page:{page}:size:{size}`.

### 5. High frontend: React Query todo cache can leak todos after account switch

Evidence: `frontend/src/features/todos/api/todos.ts:37` uses the global query key `["todos"]`. Auth login/logout only set or remove tokens in `frontend/src/features/auth/api/auth.ts` and do not clear query data.

Why this is a bug: if user A logs out and user B logs in in the same browser, React Query can serve user A's still-fresh todos to user B before any refetch.

Fix direction: clear React Query on auth transitions and scope todo query keys by authenticated user or session plus request params.

### 6. Medium backend: todo list cache is never invalidated after mutations

Evidence: list responses are cached in `backend/app/api/v1/todos.py:72`. Create has no Redis dependency or invalidation, while update/delete inject Redis at `backend/app/api/v1/todos.py:111` and `backend/app/api/v1/todos.py:142` but never delete or expire cache entries.

Why this is a bug: users can see stale todo lists for up to five minutes after create, update, or delete. Combined with the global key issue, stale cross-user data can persist too.

Fix direction: invalidate user-scoped list keys after every todo mutation, or use a per-user cache version in the key.

### 7. Medium backend: todo update cannot set `completed` to false and can erase description accidentally

Evidence: `TodoUpdate.completed` allows `False` in `backend/app/schemas/todo.py:15`, but `backend/app/api/v1/todos.py:123` applies it only when truthy. The update route also uses `todo_data.model_dump()`, which includes omitted nullable fields as `None`; `backend/app/api/v1/todos.py:129` can clear `description` even when the client omitted it.

Why this is a bug: clients cannot mark completed todos incomplete, and unrelated updates can erase descriptions.

Fix direction: use `todo_data.model_dump(exclude_unset=True)` and apply provided fields directly, including `completed=False`.

### 8. Medium backend: email uniqueness is not enforced at the database layer

Evidence: registration checks for an existing user in `backend/app/api/v1/auth.py:28`, but `User.email` has no database unique constraint in the model or initial migration. Login lookup uses `scalar_one_or_none()` in `backend/app/services/auth_service.py:11`.

Why this is a bug: concurrent registrations can create duplicate emails, and later login can raise `MultipleResultsFound` instead of authenticating deterministically.

Fix direction: add a unique database constraint or index on `users.email`, normalize emails consistently, and handle `IntegrityError` during registration.

### 9. Medium frontend: current-user cache can show the wrong identity after account switch

Evidence: `frontend/src/features/auth/hooks/useAuth.ts:17` uses global query key `["currentUser"]`, and auth mutations do not invalidate or remove that query.

Why this is a bug: after logging out and logging in as another user, the app can reuse the previous user's cached `/auth/me` response and display the wrong email while the token belongs to a different account.

Fix direction: remove `["currentUser"]` on logout/login/register, or include a stable auth/session/user discriminator in the key once known.

### 10. Medium frontend: failed optimistic todo updates are never rolled back

Evidence: `frontend/src/features/todos/api/todos.ts:81` snapshots `previousTodos` and mutates the cache, but `frontend/src/features/todos/api/todos.ts:95` only shows a toast on error and never restores the snapshot.

Why this is a bug: if a toggle or edit request fails and the invalidating refetch also fails or is delayed, the UI can keep showing a completed or edited todo that the backend rejected.

Fix direction: use the mutation context in `onError` and restore `previousTodos` with `queryClient.setQueryData`.

### 11. Medium frontend: global 401 redirect can break auth error handling

Evidence: `frontend/src/lib/api.ts:30` redirects on every 401. Login form code expects to handle login errors locally with a toast.

Why this is a bug: if the backend returns 401 for invalid credentials, the interceptor can force navigation before endpoint-specific error handling completes. It also prevents routes from handling expected 401s differently.

Fix direction: redirect only for protected requests that had an existing token, or exclude `/auth/login`, `/auth/register`, and other auth endpoints from the global redirect path.


### 12. Medium backend: todo page size is unbounded

Evidence: `backend/app/api/v1/todos.py:40` declares `size: int = Query(20, ge=1)` without an upper bound, and `backend/app/services/todo_service.py:31` passes that value directly into the SQL `LIMIT`.

Why this is a bug: a single request can force large database reads, expensive JSON serialization, and large Redis cache writes, creating an avoidable denial-of-service and latency risk.

Fix direction: add a practical upper bound such as `Query(20, ge=1, le=50)` and add a backend test proving oversized page requests are rejected.

### 13. Medium backend: todo listing performs N+1 user queries

Evidence: `backend/app/api/v1/todos.py:58` iterates todos and `backend/app/api/v1/todos.py:60` executes `select(User).where(User.id == todo.user_id)` inside the loop.

Why this is a bug: listing performance degrades linearly with page size and adds unnecessary database round trips under normal usage.

Fix direction: populate `user_email` from `current_user.email` for user-scoped lists, or move response construction into a joined/selectin-loaded service query if the endpoint later needs cross-user listing.

### 14. Medium backend: todo cache can be repopulated stale before commit

Evidence: `backend/app/db/session.py:25` commits after the route returns, but create, update, and delete invalidate cache inside the route at `backend/app/api/v1/todos.py:97`, `backend/app/api/v1/todos.py:136`, and `backend/app/api/v1/todos.py:157`.

Why this is a bug: a concurrent list request can run between cache invalidation and transaction commit, read the old database state, and repopulate Redis with stale todo data.

Fix direction: commit the mutation before cache invalidation, or introduce an after-commit invalidation mechanism so Redis is cleared only after the database state is durable.

### 15. High frontend: todo page size violates backend contract

Evidence: `frontend/src/features/todos/api/todos.ts:41` declares `useTodos(page: number = 1, size: number = 10000)`, and `frontend/src/features/todos/api/todos.ts:48` sends that size to `/todos`.

Why this is a bug: the dashboard's initial todo request can fail with backend validation instead of loading todos, and the frontend contract drifts from the API contract.

Fix direction: default the frontend page size to 50 or less, then add pagination or infinite loading in `TodoPage` using `data.total`, `data.page`, and `data.size`.

### 16. Medium frontend: refresh token is stored in localStorage

Evidence: `frontend/src/features/auth/api/session.ts:22` writes tokens through `setAuthTokens`, and `frontend/src/features/auth/api/session.ts:23` through `frontend/src/features/auth/api/session.ts:24` store both `access_token` and `refresh_token` in localStorage.

Why this is a bug: any XSS vulnerability can steal the long-lived refresh token and allow session replay until server-side revocation or expiry.

Fix direction: prefer storing refresh tokens in HttpOnly, Secure, SameSite cookies. If bearer tokens must remain, keep refresh tokens out of persistent JavaScript-readable storage and rotate short-lived access tokens aggressively.

### 17. Medium frontend: todo actions are hidden from touch and keyboard users

Evidence: `frontend/src/features/todos/components/TodoItem.tsx:39` uses `opacity-0 group-hover:opacity-100` for the action container.

Why this is a bug: users on mobile, tablets, or keyboard navigation can lose access to core todo actions or focus invisible controls.

Fix direction: keep actions visible by default, or add `focus-within:opacity-100` plus responsive behavior that shows actions on coarse-pointer devices.

### 18. Medium frontend: todo list uses array index keys

Evidence: `frontend/src/features/todos/components/TodoList.tsx:40` maps `(todo, index)`, and `frontend/src/features/todos/components/TodoList.tsx:42` passes `key={index}`.

Why this is a bug: React can reuse DOM nodes incorrectly after insertions or deletions, causing focus, checkbox, or edit-state glitches.

Fix direction: use the stable todo identifier as the key, `key={todo.id}`, and remove the unused `index` prop if it is not needed.

