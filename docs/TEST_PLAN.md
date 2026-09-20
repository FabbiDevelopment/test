# Manual Test Plan: Fabbi Todo App — Authentication, Authorization & Todo CRUD

## 1. Scope & Objective

- **Objective:** Validate core application features and perform regression testing for all bugs fixed in Tier 1.
- **Scope:** Authentication, Authorization, Todo CRUD operations, Business Logic, Caching, and Security boundaries.

## 2. Test Environment & Prerequisites

- **Backend Base URL:** `http://localhost:8000`
- **Frontend Base URL:** `http://localhost:3000`
- **API Documentation:** `http://localhost:8000/docs`
- **Application Startup:** `docker-compose up --build`
- **Pre-seeded User Accounts (after seeding):**
  - User A: `user_a@test.com` / `Password@123`
  - User B: `user_b@test.com` / `Password@123`
- **Tools Required:** Browser DevTools, Postman / curl, Docker container logs

---

## 3. Test Cases Matrix

| TC ID | Module | Test Scenario | Preconditions | Test Steps | Expected Result | Priority / Severity | Status |
|-------|--------|--------------|---------------|------------|-----------------|---------------------|--------|
| TC-01 | Auth | Successful User Registration | Account does not exist | 1. Navigate to `/register`<br>2. Enter valid email + password<br>3. Submit | HTTP 201, returns `access_token` + `refresh_token`, redirects to `/` | High / Blocker | PASSED |
| TC-02 | Auth | Register Existing Email | Email already registered | 1. Send POST `/auth/register` with duplicate email | HTTP 400 `"Email already registered"` | High / Critical | PASSED |
| TC-03 | Auth | Successful Login | User is registered | 1. Navigate to `/login`<br>2. Enter valid email + password<br>3. Submit | HTTP 200, returns token pair, redirects to `/` | High / Blocker | PASSED |
| TC-04 | Auth | Login Non-existent Email (No User Enumeration) | Email not registered | 1. Send POST `/auth/login` with non-existent email | HTTP 401, generic message `"Invalid email or password"` (**not** 404) | Medium / Security | PASSED |
| TC-05 | Auth | Login Invalid Password | User is registered | 1. Enter valid email with incorrect password | HTTP 401, generic message `"Invalid email or password"` | Medium / Security | PASSED |
| TC-06 | Auth | Access Protected Endpoint Without Token | User not authenticated | 1. Send GET `/api/v1/todos` without `Authorization` header | HTTP 401 / 403 Unauthorized | High / Critical | PASSED |
| TC-07 | Auth | Expired JWT Token Rejection | Token has expired | 1. Send request with an expired access token | HTTP 401 `"Invalid authentication token"` | High / Critical | PASSED |
| TC-08 | Auth | Logout Revokes Access Token | User is logged in | 1. POST `/auth/logout`<br>2. Reuse revoked token for GET `/auth/me` | HTTP 401 `"Token has been revoked"` | High / Critical | PASSED |
| TC-09 | Auth | Valid Refresh Token Grants New Pair | User is logged in | 1. POST `/auth/refresh` with valid refresh token | HTTP 200, receives new `access_token` and `refresh_token` | Medium / High | PASSED |
| TC-10 | Auth | Refresh Token Reuse After Rotation | Token already refreshed | 1. Reuse old `refresh_token` on POST `/auth/refresh` | HTTP 401 `"Refresh token has been revoked"` | Medium / Security | PASSED |
| TC-11 | Authorization | User A Cannot Read User B's Todo | Users A & B have todos | 1. User B creates a todo<br>2. User A sends GET `/todos/{User_B_Todo_ID}` | HTTP 403 Forbidden | High / Critical | PASSED |
| TC-12 | Authorization | User A Cannot Update User B's Todo | Users A & B have todos | 1. User B creates a todo<br>2. User A sends PUT `/todos/{User_B_Todo_ID}` | HTTP 403 Forbidden | High / Critical | PASSED |
| TC-13 | Authorization | User A Cannot Delete User B's Todo | Users A & B have todos | 1. User B creates a todo<br>2. User A sends DELETE `/todos/{User_B_Todo_ID}` | HTTP 403 Forbidden | High / Critical | PASSED |
| TC-14 | Authorization | User A Only Sees Own Todos | Both users have todos | 1. User A sends GET `/todos`<br>2. Inspect response list | Returns only User A's todos; User B's todos are hidden | High / Critical | PASSED |
| TC-15 | Todo CRUD | Create Todo Success | User is logged in | 1. Send POST `/todos` with valid title | HTTP 201, todo created with `completed: false` | High / Blocker | PASSED |
| TC-16 | Todo CRUD | Create Todo Missing Title Validation | User is logged in | 1. Send POST `/todos` with empty body `{}` or `{"title": ""}` | HTTP 422 Validation Error | Medium / Major | PASSED |
| TC-17 | Todo CRUD | Toggle `completed` from `true → false` | Todo is `completed: true` | 1. Send PUT `/todos/{id}` with `{"completed": false}`<br>2. Refetch todo | `completed: false` is correctly persisted | Medium / Major | PASSED |
| TC-18 | Todo CRUD | Update Title Preserves Description | Todo has title + description | 1. Send PUT `/todos/{id}` with `{"title": "Updated Title"}`<br>2. Refetch todo | `description` remains intact, `title` updated | Medium / Major | PASSED |
| TC-19 | Todo CRUD | Delete Todo | Todo exists | 1. Send DELETE `/todos/{id}`<br>2. Send GET `/todos/{id}` | HTTP 204 on delete, HTTP 404 on subsequent fetch | High / Major | PASSED |
| TC-20 | Caching | Create Todo Invalidates Stale Cache | Cache is active | 1. GET `/todos` (populates cache)<br>2. POST `/todos`<br>3. GET `/todos` again | New todo appears in list immediately (cache invalidated) | Medium / Major | PASSED |
| TC-21 | Caching | Isolated Cache Keys per User | Both users logged in | 1. User A sends GET `/todos`<br>2. User B sends GET `/todos` | User B receives User B's cached list, not User A's | High / Critical | PASSED |

---

## 4. Defect Tracking & Known Limitations

### Fixed Bugs (Tier 1 Regression Coverage)

| Bug ID | Fixed Defect | Test Case Mapping |
|--------|--------------|-------------------|
| **Bug #1** | Disabled JWT Expiration Verification | TC-07 |
| **Bug #2** | Global Shared Redis Cache Key Leak | TC-14, TC-21 |
| **Bug #3** | Missing Ownership Check on GET/PUT/DELETE | TC-11, TC-12, TC-13 |
| **Bug #4** | Unable to Toggle `completed` `true → false` | TC-17 |
| **Bug #5** | Cache Not Invalidated on Mutation | TC-20 |
| **Bug #6** | User Enumeration via HTTP 404 on Login | TC-04, TC-05 |
| **Bug #7** | Refresh Token JTI Not Rotated/Revoked | TC-10 |
| **Bug #8** | Logout Fails to Blacklist Access Token | TC-08 |
| **Bug #9** | Missing DB Unique Constraint on `users.email` | TC-02 |

### Known Limitations & Testing Notes

- **TC-07 (Expired Token):** Manual testing requires waiting 30 minutes for default JWT expiration. Automated unit tests verify expiration instantly via mocked tokens, or temporarily set `ACCESS_TOKEN_EXPIRE_MINUTES=1` in `.env`.
- **TC-21 (Cache Isolation):** Manual testing requires two isolated browser sessions (e.g., standard window and Incognito window).
- **Playwright E2E Suites:** Require `docker-compose up` services to be active prior to execution.
