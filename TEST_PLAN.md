# Manual Test Plan: Authentication, Authorization, Todo, and Cache Regression

## 1. Scope and objective

Validate the critical authentication and todo workflows, authorization boundaries, partial-update semantics, cache consistency, and account-session isolation addressed in Tiers 1 and 2.

Out of scope: load testing, browser compatibility outside current Chrome, password reset, email verification, refresh-token revocation, and the optional Tier 4 feature set.

## 2. Environment and prerequisites

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API documentation: `http://localhost:8000/docs`
- Supported browser for this pass: latest Chrome
- Services running: frontend, backend, PostgreSQL, and Redis
- User A: a newly registered account with no initial todos
- User B: a different newly registered account with no initial todos
- Tester can inspect HTTP status and response bodies using browser developer tools or an API client

Status values: `Not Run`, `Pass`, `Fail`, or `Blocked`.

## 3. Test cases

| ID | Area | Scenario | Preconditions | Steps | Expected result | Priority / Severity | Actual result | Status |
|---|---|---|---|---|---|---|---|---|
| AUTH-01 | Registration | Register with valid credentials | Email is unused | Open Register; enter valid email/password/confirmation; submit | HTTP 201; tokens stored; user lands on My Todos | P0 / Critical | Not recorded | Not Run |
| AUTH-02 | Registration | Reject duplicate email | Existing registered user | Register again with the same email | HTTP 400; no second account; useful error displayed | P1 / Major | Not recorded | Not Run |
| AUTH-03 | Login | Login with correct credentials | Registered user is logged out | Enter correct email/password; submit | HTTP 200; user lands on My Todos | P0 / Critical | Not recorded | Not Run |
| AUTH-04 | Login | Reject incorrect password without granting access | Registered user is logged out | Enter correct email and wrong password; submit | HTTP 401; no tokens stored; protected page remains inaccessible | P0 / Critical | Not recorded | Not Run |
| AUTH-05 | Token | Reject tampered access token | Any registered user | Change one character in token; call `GET /auth/me` | HTTP 401; no user data returned | P0 / Critical | Not recorded | Not Run |
| AUTH-06 | Token | Reject expired access token | Expired signed token is available | Call `GET /auth/me` with expired token | HTTP 401; user is redirected to login | P0 / Critical | Not recorded | Not Run |
| AUTH-07 | Token | Reject refresh token on protected API | Valid refresh token is available | Use refresh token as Bearer token for `GET /auth/me` | HTTP 401 | P0 / Critical | Not recorded | Not Run |
| AUTH-08 | Logout | Clear session and cached user data | User has loaded todos | Click Logout; use browser Back; then log in as another user | Login page remains protected; previous user's todos never appear | P0 / Critical | Not recorded | Not Run |
| TODO-01 | CRUD | Create and retrieve a todo | User A is logged in | Create todo with title/description; reload page | Todo persists with exact values and incomplete state | P0 / Critical | Not recorded | Not Run |
| TODO-02 | Update | Toggle completed true then false | User A owns a todo | Check todo; reload; uncheck; reload | Each state persists, including explicit `false` | P1 / Major | Not recorded | Not Run |
| TODO-03 | Update | Partial title update preserves description | User A owns todo with description | Send update containing only title | Title changes; description remains unchanged | P1 / Major | Not recorded | Not Run |
| TODO-04 | Update | Explicit null clears description | User A owns todo with description | Send update with `description: null` | Description is cleared and other fields remain unchanged | P2 / Minor | Not recorded | Not Run |
| TODO-05 | Delete | Delete owned todo | User A owns a todo | Delete todo; reload/list todos | HTTP 204; todo remains absent | P1 / Major | Not recorded | Not Run |
| AUTHZ-01 | Isolation | User B cannot list User A's todo | User A owns a uniquely named todo; User B is logged in separately | User B loads todo list | User A's title/content is absent | P0 / Critical | Not recorded | Not Run |
| AUTHZ-02 | Isolation | User B cannot read User A's todo by ID | User B knows User A's todo ID | User B calls `GET /todos/{id}` | HTTP 404; no todo content returned | P0 / Critical | Not recorded | Not Run |
| AUTHZ-03 | Isolation | User B cannot update User A's todo | User B knows User A's todo ID | User B calls `PUT /todos/{id}` | HTTP 404; owner later sees unchanged todo | P0 / Critical | Not recorded | Not Run |
| AUTHZ-04 | Isolation | User B cannot delete User A's todo | User B knows User A's todo ID | User B calls `DELETE /todos/{id}` | HTTP 404; owner can still retrieve todo | P0 / Critical | Not recorded | Not Run |
| CACHE-01 | Isolation | List cache is isolated per user | User A list has been loaded and cached | User B immediately loads the same page/size | Only User B's todos are returned | P0 / Critical | Not recorded | Not Run |
| CACHE-02 | Invalidation | Create invalidates cached list | User A has cached an empty list | Create todo; reload list | New todo appears immediately | P1 / Major | Not recorded | Not Run |
| CACHE-03 | Invalidation | Update invalidates all cached pages | User A has cached multiple list pages | Update a todo; revisit affected page | Updated values appear; no stale version returned | P1 / Major | Not recorded | Not Run |
| CACHE-04 | Invalidation | Delete invalidates cached list | User A has cached a list | Delete todo; reload list | Deleted todo does not reappear | P1 / Major | Not recorded | Not Run |
| PAGE-01 | Pagination | Cache and UI respect page/size parameters | User owns more todos than one page | Request page 1 and page 2 with same size | Pages contain correct, non-interchanged results and totals | P2 / Major | Not recorded | Not Run |

## 4. Automated coverage mapping

- Backend: `backend/tests/test_auth.py` covers registration, login, current user, logout, expiration, and token type.
- Backend: `backend/tests/test_todos.py` covers CRUD, ownership boundaries, boolean/partial updates, and cache invalidation.
- Browser: `frontend/e2e/todo.spec.ts` covers the full user journey and cross-session data isolation.

## 5. Entry and exit criteria

Entry: services are healthy, migrations are applied, test users can be created, and no unrelated P0 incident blocks authentication.

Exit: all P0 and P1 cases pass; no open Critical or Blocker defect; automated backend and E2E suites pass; any accepted P2 issue is documented with an owner.

## 6. Defect reporting

For each failure record environment, test-case ID, reproducible steps, expected and actual behavior, HTTP request/response with secrets removed, screenshot or trace where useful, severity, and affected build/commit.

## 7. Known limitations and risks

- Logout is client-side and does not revoke already issued JWTs server-side.
- E2E uses isolated SQLite and in-memory cache for deterministic functional coverage; PostgreSQL/Redis integration should also be smoke-tested in Docker before release.
- Automated browser coverage currently targets Chromium only.
