# Tier 1: Bug Hunting & Critical Fixes Report

## Overview
This document details the intentional security flaws, authorization holes, business logic bugs, caching issues, performance bottlenecks, and state management defects identified across the codebase.

---

### Bug 1: JWT Expiration Verification Disabled
- **Location**: `backend/app/core/security.py`, function `verify_token()`, line 56
- **Severity**: Critical
- **Reason**: The `jwt.decode()` call explicitly specifies `options={"verify_exp": False}`. This completely bypasses token expiration verification, allowing expired, revoked, or leaked access tokens to remain valid indefinitely.
- **Fix Proposal**: Remove `options={"verify_exp": False}` so that `python-jose` enforces the `exp` claim verification by default and raises `ExpiredSignatureError` upon expired tokens.

---

### Bug 2: Broken Object Level Authorization (IDOR / BOLA) on Todo Resources
- **Location**: `backend/app/api/v1/todos.py`, functions `get_todo()`, `update_existing_todo()`, and `delete_existing_todo()`, lines 89–154
- **Severity**: Critical
- **Reason**: The endpoints fetch todos by `todo_id` without verifying that `todo.user_id == current_user.id`. Any authenticated user (User A) can view, modify, or delete todos owned by any other user (User B) simply by passing the target UUID.
- **Fix Proposal**: Add an ownership check after retrieving the todo:
  ```python
  if todo.user_id != current_user.id:
      raise HTTPException(
          status_code=status.HTTP_403_FORBIDDEN,
          detail="Not authorized to access this todo"
      )
  ```
  Or query directly with compound filter: `WHERE id = :todo_id AND user_id = :current_user_id`.

---

### Bug 3: Boolean Toggle Failure on `completed` Status
- **Location**: `backend/app/api/v1/todos.py`, function `update_existing_todo()`, lines 123–124
- **Severity**: High
- **Reason**: The code evaluates `if todo_data.completed:`. When a client attempts to uncheck a completed todo (`{"completed": false}`), the condition evaluates to `False` in Python, preventing the field from ever being persisted back to `False`.
- **Fix Proposal**: Update the condition to explicitly check for `None`:
  ```python
  if todo_data.completed is not None:
      todo.completed = todo_data.completed
  ```

---

### Bug 4: Partial Update Erasing Todo Description
- **Location**: `backend/app/api/v1/todos.py`, function `update_existing_todo()`, lines 121–131
- **Severity**: High
- **Reason**: Calling `todo_data.model_dump()` returns all fields, including unset fields as `{"description": None}`. The subsequent check `if "description" in update_data:` evaluates to `True`, overwriting the existing description with `None` when only `title` was sent in the request.
- **Fix Proposal**: Use `exclude_unset=True` when dumping the model:
  ```python
  update_data = todo_data.model_dump(exclude_unset=True)
  ```

---

### Bug 5: Shared Global Redis Cache Key & Missing Cache Invalidation
- **Location**: `backend/app/api/v1/todos.py`, function `list_todos()` (line 37) and mutating endpoints (`create_new_todo`, `update_existing_todo`, `delete_existing_todo`)
- **Severity**: Critical
- **Reason**:
  1. The cache key is statically hardcoded as `"todos:list"`. When User A fetches their list, it gets cached under `"todos:list"`. When User B requests their list, Redis serves User A's todos to User B (Cross-user data leak).
  2. None of the mutating operations (create, update, delete) invalidate the Redis cache, serving stale data for the entire 5-minute TTL.
- **Fix Proposal**:
  1. Scope cache keys per user and pagination params: `f"todos:user:{current_user.id}:page:{page}:size:{size}"`.
  2. Invalidate all user-scoped keys upon any todo creation, update, or deletion.

---

### Bug 6: Incomplete Logout Flow (Tokens and Query Cache Not Cleared)
- **Location**: `frontend/src/features/auth/hooks/useAuth.ts`, function `logout()`, lines 23–35
- **Severity**: High
- **Reason**: In `useAuth.logout()`, the mutation success handler does not clear `localStorage` or `queryClient` cache consistently. A subsequent user logging in on the same browser session can see the previous user's stale query cache in memory.
- **Fix Proposal**: In `onSuccess` and `onError`, remove tokens from `localStorage` and call `queryClient.clear()` before navigating to `/login`.

---

### Bug 7: Optimistic Update Lacks Rollback on Mutation Error
- **Location**: `frontend/src/features/todos/api/todos.ts`, function `useUpdateTodo()`, lines 95–97
- **Severity**: Medium
- **Reason**: `onMutate` captures `previousTodos` in context, but `onError` only displays a toast and fails to restore `previousTodos` into `queryClient`. If the server request fails, the UI remains in a desynchronized optimistic state.
- **Fix Proposal**: Implement rollback in `onError`:
  ```typescript
  onError: (_err, _newTodo, context) => {
    if (context?.previousTodos) {
      queryClient.setQueryData(["todos"], context.previousTodos);
    }
    toast.error("Failed to update todo");
  },
  ```

---

### Bug 8: TanStack Query Key Missing Pagination Dependencies & Hardcoded 10,000 Size
- **Location**: `frontend/src/features/todos/api/todos.ts`, function `useTodos()`, lines 35–44
- **Severity**: High
- **Reason**:
  1. The query key is statically set to `["todos"]` without including `page` and `size`. Navigating between different pages causes TanStack Query to serve cached data from the first loaded page instead of fetching the new page.
  2. Default `size = 10000` fetches excessive records at once, defeating server-side pagination and degrading performance.
- **Fix Proposal**: Set query key with dependencies: `queryKey: ["todos", { page, size }]` and set a sensible default `size` (e.g. 10 or 20).

---

### Bug 9: Axios Interceptor 401 Loop & Login Error Swallowing
- **Location**: `frontend/src/lib/api.ts`, lines 27–37
- **Severity**: High
- **Reason**: The global response interceptor catches all `401 Unauthorized` responses and immediately executes `window.location.href = "/login"`. When a user enters incorrect credentials on `/login`, the backend returns 401; the interceptor forces a page reload, wiping out form inputs, React state, and toast notifications before the user can read the error message.
- **Fix Proposal**: Exclude authentication routes from redirect, and implement a proper token refresh retry flow:
  ```typescript
  if (error.response?.status === 401 && !error.config?.url?.includes("/auth/login")) {
    // Attempt token refresh or redirect
  }
  ```

---

### Bug 10: Non-Deterministic Todo Ordering & Array Index Used as React Key (Items Shifting Positions)
- **Location**:
  1. `backend/app/services/todo_service.py`, function `get_todos()`, line 31
  2. `frontend/src/features/todos/components/TodoList.tsx`, line 42
- **Severity**: High
- **Reason**:
  1. The database query in `get_todos()` lacked an `ORDER BY` clause. Due to PostgreSQL's MVCC mechanism, updating a todo (e.g. toggling `completed`) writes a new row version to a different disk page, causing subsequent `SELECT` queries to return items in an unpredictable, shifting order.
  2. Rendering items with `key={index}` instead of `key={todo.id}` causes React's reconciliation algorithm to mishandle internal DOM state when items are updated, reordered, or deleted.
- **Fix Proposal**:
  1. Enforce deterministic sorting in `get_todos()`: `.order_by(Todo.created_at.desc(), Todo.id.desc())`.
  2. Replace `key={index}` with `key={todo.id}` in `TodoList.tsx`.

---

### Bug 11: TodoForm Component Not Resetting on Active Todo Changes
- **Location**: `frontend/src/features/todos/components/TodoForm.tsx`, lines 34–37
- **Severity**: Medium
- **Reason**: `useForm` initializes `defaultValues` only once on mount. When switching between editing different todos, the form retains stale values from the previously edited todo.
- **Fix Proposal**: Add a `useEffect` hook listening to changes in `todo` and invoke `reset()` with the updated todo values.

---

### Bug 12: N+1 Query Problem on Todo List Fetching
- **Location**: `backend/app/api/v1/todos.py`, lines 48–50
- **Severity**: Medium
- **Reason**: Inside the loop constructing `items`, the endpoint executes an individual SQL query `SELECT * FROM users WHERE id = :user_id` for every single todo item, resulting in N+1 database queries.
- **Fix Proposal**: Since all fetched todos belong to `current_user`, assign `user_email=current_user.email` directly without querying the database inside the loop.

---

### Bug 13: User Enumeration Vulnerability in Login Endpoint
- **Location**: `backend/app/api/v1/auth.py`, lines 54–58
- **Severity**: Low / Security
- **Reason**: The login endpoint returns `404 Not Found` with detail `"User with this email not found"`, while returning `401 Unauthorized` for an incorrect password. This allows malicious actors to enumerate valid user email addresses.
- **Fix Proposal**: Return a generic `401 Unauthorized` with `"Incorrect email or password"` for both missing user and invalid password cases.

---

### Bug 14: Refresh Token Usable as Access Token
- **Location**: `backend/app/api/deps.py`, lines 20–28
- **Severity**: Medium
- **Reason**: `get_current_user` extracts and decodes the bearer token, but does not verify `payload.get("type") == "access"`. This allows a refresh token to be used directly to authorize protected API endpoints.
- **Fix Proposal**: Check that `payload.get("type") == "access"` in `get_current_user`.
