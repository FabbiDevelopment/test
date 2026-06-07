# Functional Bug Fix Summary

Date: 2026-06-07

This document summarizes the functional bugs that were fixed and the solution approach for each one. It intentionally omits code.

## Backend Fixes

### Expired JWTs were accepted indefinitely

Bug: JWT expiration was not enforced during token verification, so expired access and refresh tokens could still be used.

Solution: Token verification now enforces expiration. Expired access tokens are rejected on protected routes, and expired refresh tokens are rejected by the refresh endpoint.

### Refresh tokens could access protected API routes

Bug: Protected routes accepted any valid token with a user subject, including refresh tokens.

Solution: Protected route authentication now requires an access token. Refresh tokens are only valid for the refresh endpoint.

### Users could access other users' todos by UUID

Bug: Single todo get, update, and delete routes looked up todos only by todo ID, without checking the authenticated owner.

Solution: Item-level todo operations now scope lookups to the current user. A user cannot read, update, or delete another user's todo even if they know the UUID.

### Todo list cache leaked across users and pages

Bug: Redis used one global todo list cache key for every user and pagination request.

Solution: Todo list cache keys now include the authenticated user ID, page, and page size. Cached list responses are isolated by user and request parameters.

### Todo list cache stayed stale after mutations

Bug: Creating, updating, or deleting todos did not invalidate cached todo lists.

Solution: Todo mutations now invalidate the current user's cached todo list entries so the next list request reflects the latest data.

### Todo partial updates mishandled omitted fields and `completed: false`

Bug: Updating a todo could not set `completed` to false, and omitted nullable fields could be treated as explicit null values.

Solution: Todo updates now apply only fields provided by the client. Boolean false values are preserved, and omitted fields are left unchanged.

### Duplicate user emails were not protected at the database layer

Bug: Registration checked for existing emails in application code only, leaving a race condition where duplicate emails could be inserted.

Solution: User email uniqueness is enforced at the database layer with a migration, and registration handles duplicate insert races as an email conflict.

### Settings parsing rejected unrelated environment values

Bug: Pydantic settings could reject extra environment values, which made local and Docker environments more fragile.

Solution: Settings now ignore unrelated environment keys using the Pydantic v2 configuration style.

## Frontend Fixes

### Todo cache could leak after switching accounts

Bug: React Query used a global todo query key, so a second user in the same browser could temporarily see the first user's cached todos.

Solution: Todo query keys now include request parameters and the current auth session. Auth transitions clear todo cache data.

### Current user cache could show the wrong identity

Bug: The current-user query used a global key and was not cleared during account changes.

Solution: The current-user query is now scoped by auth session, and login, register, logout, and forced auth cleanup remove stale user cache entries.

### Failed optimistic todo updates were not rolled back

Bug: The UI optimistically changed cached todos, but failed update requests did not restore the previous cache state.

Solution: Optimistic updates now snapshot all affected todo list caches and restore them on request failure.

### Global 401 handling interrupted login/register errors

Bug: The API interceptor redirected to login for every 401 response, including invalid login attempts that should be handled by the form.

Solution: The redirect now only happens for protected requests that had an auth token. Login and register errors are left for the page-level UI to handle.

### Token and session handling was duplicated

Bug: Token storage and auth session behavior were spread across multiple frontend modules.

Solution: Auth token and session handling were centralized in a shared helper so login, register, logout, API requests, and query keys all use consistent session state.

## Verification

Backend:
- Test suite passed: 17 passed.
- Black check passed.
- Flake8 passed.

Frontend:
- ESLint passed.
- TypeScript build check passed.
- Vite production build passed.

Known warnings:
- Backend tests still emit a pytest-asyncio deprecation warning for the custom event loop fixture.
- Frontend build still emits the existing Vite chunk-size warning.

### Todo cache invalidation now waits for commit

Bug: Todo mutation routes invalidated Redis list-cache entries before the request-scoped database dependency committed the transaction, allowing a concurrent list request to repopulate cache from stale database state.

Solution: Todo create, update, and delete routes now explicitly commit successful mutations before invalidating the current user's todo list cache. A regression test observes committed database state from a separate session during invalidation for create, update, and delete.

### Todo list page size is now bounded

Bug: The todo list endpoint accepted any positive page size and passed it directly to the database query and Redis response cache.

Solution: Todo list requests now cap `size` at 50 using FastAPI query validation. Oversized page requests are rejected before they can trigger large database reads, response serialization, or cache writes.

### Todo list no longer does per-row user lookups

Bug: The todo list route queried the users table once per todo row even though the endpoint only returns todos owned by the authenticated user.

Solution: Todo list response construction now uses the authenticated user's email for `user_email`, removing the per-item user lookup. A focused regression test verifies list rendering does not execute a user lookup while still returning the expected email.

### Todo page size now matches the backend contract

Bug: The frontend defaulted todo list requests to `size=10000`, which violates the backend page-size contract and can make the dashboard fail its initial load.

Solution: Todo queries now default to a backend-compatible page size of 50, and the todo page includes previous/next pagination controls driven by the API response totals.

### Refresh tokens are no longer persisted in localStorage

Bug: The frontend persisted refresh tokens in JavaScript-readable localStorage.

Solution: The session helper now persists only the access token and session marker, and it removes any legacy refresh token entry when new tokens are stored or auth state is cleared.

### Todo actions are visible without hover

Bug: Todo edit and delete actions were hidden until hover, which made core actions inaccessible or invisible on touch and keyboard workflows.

Solution: Todo item actions are now visible by default instead of depending on hover-only opacity.

### Todo rows now use stable React keys

Bug: The todo list used array indexes as React keys for a mutable list.

Solution: Todo rows now use each todo's stable `id` as the React key, and the unused index prop was removed.

## Verification

Backend:
- Test suite passed: 20 passed.
- Focused todo regression suite passed: 12 passed.

Frontend:
- TypeScript build check passed.
- Vite production build passed.
- ESLint could not run because this shell could not resolve `npm` or `node`, including through the local eslint wrapper.

Known warnings:
- Backend tests still emit a pytest-asyncio deprecation warning for the custom event loop fixture.
- Frontend build still emits the existing Vite chunk-size warning.
