# Manual Test Plan

## Scope

Regression coverage for authentication, authorization, todo CRUD, cache invalidation, and session isolation.

## Environment and Preconditions

- Start services with `docker compose up --build`.
- Frontend: `http://localhost:3000`; API: `http://localhost:8000`.
- Use two unique accounts for each run. Do not reuse production credentials.
- Inspect API status and browser UI after every mutation.

## Test Matrix

| ID | Scenario | Preconditions and steps | Expected result | Priority | Severity |
|---|---|---|---|---|---|
| MT-01 | Register and login | Open Register, submit valid email/password, then logout and login again | Account is created, tokens are stored, dashboard opens | P0 | Critical |
| MT-02 | Invalid credentials | Register User A, login with wrong password | Request is rejected and no dashboard data is shown | P0 | High |
| MT-03 | Expired access token | Replace access token with an expired JWT and open `/auth/me` | API returns `401`; UI clears session and redirects login | P0 | Critical |
| MT-04 | Refresh token misuse | Send refresh token as Bearer token to `/auth/me` | API returns `401` | P0 | Critical |
| MT-05 | Cross-user read | User A creates todo; User B requests its ID | Response is `404`; title/description is not disclosed | P0 | Critical |
| MT-06 | Cross-user update/delete | Repeat with PUT and DELETE as User B | Both operations return `404`; User A's todo is unchanged | P0 | Critical |
| MT-07 | Boolean toggle | Create todo, mark complete, uncheck, refresh | `completed` remains `false` after refresh | P1 | Major |
| MT-08 | Partial update | Create with description; change title only | Existing description remains unchanged | P1 | Major |
| MT-09 | Cache invalidation | Load list, create/update/delete todo, reload list | New state appears immediately; stale response is not served | P1 | Major |
| MT-10 | Session isolation | Login User A in context 1, User B in context 2 | User B never sees User A's list or cached data | P0 | Critical |
| MT-11 | Duplicate email | Register same email twice, including casing variation | Second registration is rejected without duplicate user | P1 | Major |
| MT-12 | Cold boot | Stop services and run `docker compose up` | Backend waits for healthy PostgreSQL/Redis before startup | P1 | Major |

## Actual Results

Record execution date, tester, browser, commit, actual status, and defect ID beside each case during acceptance. Automated backend results are tracked in the assessment report; browser E2E results are produced by Playwright.

## Known Limitations

The backend test fixture uses SQLite while production uses PostgreSQL and Redis. PostgreSQL index plans and Docker startup must therefore be validated separately in the integration environment.
