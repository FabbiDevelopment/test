# Manual Test Plan: Authentication, Todo CRUD, Authorization and Caching

## 1. Scope and objective

Validate the authentication flow, Todo CRUD operations, authorization boundaries,
cache invalidation, token revocation, pagination limits and user data isolation.

## 2. Test environment and prerequisites

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:5173`
- PostgreSQL and Redis are running.
- Database migrations have been applied.

## 3. Test cases

| ID | Area | Scenario | Steps | Expected result | Priority |
|---|---|---|---|---|---|
| TC-01 | Auth | Successful login | Register or use an existing account, then login with valid credentials | User reaches Todo page | High |
| TC-02 | Auth | Invalid credentials | Login with an incorrect password | API returns 401 and UI shows an error | Medium |
| TC-03 | Auth | Revoked access token | Call logout, then call `GET /api/v1/todos` with the old access token | API returns 401 | Critical |
| TC-04 | Auth | Revoked refresh token | Call logout with refresh token, then call `/api/v1/auth/refresh` with it | API returns 401 | Critical |
| TC-05 | Todo | Create Todo | Create a Todo and reload the list | New Todo is visible | High |
| TC-06 | Todo | Update Todo | Update title and description | New values persist after refetch | High |
| TC-07 | Todo | Toggle completion both ways | Toggle false to true, then true to false | Both transitions persist | High |
| TC-08 | Todo | Delete Todo | Delete a Todo and refetch | Deleted Todo is absent | High |
| TC-09 | Authorization | Cross-user access | User B uses User A's Todo ID for GET, PUT and DELETE | API returns 404 | Critical |
| TC-10 | Isolation | Switch users without reload | Login as A, logout, login as B in the same browser | B sees only B's Todos | Critical |
| TC-11 | Pagination | Oversized page | Call `/api/v1/todos?size=101` | API returns 422 | Medium |
| TC-12 | Cache | Mutation invalidation | Load list, create/update/delete, then load list again | List reflects the latest database state | Medium |

## 4. Automated test commands

```bash
# Backend
cd backend
pytest tests/ -v

# Frontend build
cd frontend
npm run build

# E2E (backend must already be running)
npm run dev -- --host 0.0.0.0
npx playwright install chromium
npm run e2e
```

## 5. Known limitations

- E2E tests require a running backend and database.
- No performance benchmark is included in this manual plan.
