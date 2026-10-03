# Manual Test Plan

## 1. Overview
This test plan covers the critical flows of the FabbiTest application, specifically focusing on Authentication, Authorization, and Todo CRUD operations.

## 2. Test Scenarios

### Scenario 1: User Registration and Authentication
**Objective:** Verify that a new user can register, log in, and log out successfully.
- **Preconditions:** The user does not have an account with the test email.
- **Steps:**
  1. Navigate to `/register`.
  2. Enter a valid email and matching passwords.
  3. Submit the form.
  4. Verify redirect to the dashboard.
  5. Click "Logout" and verify redirect to `/login`.
  6. Attempt to log in with the newly created credentials.
- **Expected Result:** Registration and login succeed. Upon logout, tokens are cleared and the user is redirected to the login page.
- **Severity:** High
- **Priority:** P0

### Scenario 2: Todo Data Isolation (Authorization)
**Objective:** Verify that users can only access their own todos.
- **Preconditions:** User A and User B exist. User A has created at least one Todo.
- **Steps:**
  1. Log in as User B.
  2. View the dashboard.
  3. Attempt to directly fetch or mutate User A's Todo via API (e.g., `GET /api/v1/todos/{user_a_todo_id}`).
- **Expected Result:** The dashboard only shows User B's todos. The direct API call returns `403 Forbidden` (or `404 Not Found`).
- **Severity:** Critical
- **Priority:** P0

### Scenario 3: Todo Creation and Cache Invalidation
**Objective:** Verify that creating a new Todo updates the list immediately without stale cache issues.
- **Preconditions:** User is logged in.
- **Steps:**
  1. Note the current number of Todos.
  2. Click "Add Todo".
  3. Fill in title and description, and submit.
  4. Verify the new Todo appears in the list immediately.
  5. Reload the page.
- **Expected Result:** The new Todo is visible immediately, and remains visible after reload. The backend cache is correctly invalidated upon creation.
- **Severity:** Medium
- **Priority:** P1

### Scenario 4: User Enumeration Prevention
**Objective:** Verify that the login endpoint does not leak whether an email is registered.
- **Preconditions:** An unregistered email is known.
- **Steps:**
  1. Attempt to log in with an unregistered email and random password.
  2. Attempt to log in with a registered email but incorrect password.
- **Expected Result:** Both attempts yield the same `401 Unauthorized` response with a generic message (e.g., "Incorrect email or password").
- **Severity:** High
- **Priority:** P1
