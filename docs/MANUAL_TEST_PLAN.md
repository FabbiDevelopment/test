# Manual Test Plan: Todo Security and Regression

## 1. Scope and Environment

Validate authentication, authorization, todo CRUD, cache isolation, responsive UI and container startup at `http://localhost:3000` and `http://localhost:8000`.

Prerequisites: services are healthy; create User A and User B with unique emails; browser devtools and API client are available.

## 2. Test Matrix

| ID | Scenario | Steps | Expected | Priority / Severity | Status |
|---|---|---|---|---|---|
| AUTH-01 | Register and login | Register a valid account, logout, login again | Tokens issued and dashboard opens | High / Blocker | Not run |
| AUTH-02 | Invalid credentials | Login using unknown email and wrong password | Both return 401 with the same generic message | High / Security | Not run |
| AUTH-03 | Expired/tampered JWT | Call `GET /auth/me` with expired then modified token | Both return 401, no user data | Critical / Security | Not run |
| AUTH-04 | Refresh token as access token | Send refresh token as Bearer token | Protected endpoint returns 401 | High / Security | Not run |
| TODO-01 | CRUD journey | Create, edit title, clear description, delete | Each state persists after reload | High / Major | Not run |
| TODO-02 | Toggle both directions | Toggle false to true, then true to false and reload | Final state remains false | High / Major | Not run |
| TODO-03 | Partial update | Create with description; update title only | Description is unchanged | High / Major | Not run |
| SEC-01 | Cross-user read | User A creates todo; User B requests its ID | 404 and no todo content | Critical / Security | Not run |
| SEC-02 | Cross-user mutation | User B updates and deletes User A's todo | Both return 404; owner data unchanged | Critical / Security | Not run |
| CACHE-01 | User isolation | Warm User A list cache, then list as User B | User B never receives User A data | Critical / Security | Not run |
| CACHE-02 | Mutation invalidation | Warm list, then create/update/delete and reload | Every response reflects latest DB state | High / Major | Not run |
| PAGE-01 | Pagination bounds | Request pages and sizes 1, 100, 101 | Valid pages are stable; 101 returns 422 | Medium / Major | Not run |
| UI-01 | Mutation failure rollback | Simulate failed toggle request | Checkbox returns to server state and error toast appears | Medium / Major | Not run |
| UI-02 | Session boundary | Logout User A and login User B in same tab | No cached User A identity or todos flash | Critical / Security | Not run |
| INFRA-01 | Cold start | Start compose with empty volumes | DB/Redis become healthy before backend; UI loads | High / Blocker | Not run |
| INFRA-02 | SPA routing | Open `/login` directly and refresh | Nginx returns app, not 404 | Medium / Major | Not run |

## 3. Exit Criteria

All Critical and High cases pass, automated suites are green, no unresolved data-isolation defect remains, and failed cases include reproduction evidence and an owner.

## 4. Known Limitations

Runtime execution is pending on a machine with Python/Node or Docker installed. Status must be updated with actual results before PR submission.
