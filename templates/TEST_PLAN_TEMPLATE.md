# Manual Test Plan

## 1. Scope & Objective

### Scope

This test plan covers the main authentication and Todo features of the application:

- User registration and login
- JWT authentication
- Logout
- Todo CRUD
- Todo completion toggle
- Partial Todo update
- User authorization
- Cross-user Todo isolation
- Redis cache invalidation
- Frontend error handling

### Objective

- Check that the main user flows work as expected.
- Verify that users can only access their own Todos.
- Verify the fixes for the bugs found during the assessment.
- Perform basic regression testing after the fixes.

---

## 2. Test Environment & Prerequisites

### Environment

| Item | Value |
|---|---|
| Frontend | React + TypeScript + Vite |
| Backend | FastAPI |
| Database | PostgreSQL |
| Cache | Redis |
| Backend Tests | pytest |
| E2E Tests | Playwright |
| Browser | Chromium |
| Frontend URL | `http://localhost:5173` |
| Backend URL | `http://localhost:8000` |

### Prerequisites

- PostgreSQL is running.
- Redis is running.
- Backend is running.
- Frontend is running.
- Valid user accounts are available.
- User A and User B are different accounts.

### Test Accounts

- User A: demo@test.com / Demo@123
- User B: testb@test.com / Test@123

> If the accounts are not available, create them through the Registration page before testing.

---

## 3. Test Cases

| ID | Feature | Test Scenario | Preconditions | Steps | Expected Result | Actual Result | Priority | Severity | Status |
|---|---|---|---|---|---|---|---|---|---|
| TC-01 | Authentication | Login with valid credentials | Valid account exists | 1. Open Login page.<br>2. Enter email and password.<br>3. Click **Sign In**. | User is logged in and redirected to the Todo page. | Works as expected. | High | High | Pass |
| TC-02 | Authentication | Logout | User is logged in | 1. Click **Logout**. | User is logged out and redirected to Login page. | Works as expected. | High | High | Pass |
| TC-03 | Authentication | Expired JWT is rejected | Valid user account exists | 1. Create an expired access token.<br>2. Call a protected API endpoint. | API returns `401 Unauthorized`. | API returns `401 Unauthorized`. | Critical | Critical | Pass |
| TC-04 | Todo | Create Todo | User is logged in | 1. Click **Add Todo**.<br>2. Enter a title.<br>3. Click **Create**. | Todo is created and shown in the list. | Works as expected. | High | High | Pass |
| TC-05 | Todo | Read Todo | User owns a Todo | 1. Open the Todo list.<br>2. View the Todo. | User can view their own Todo. | Works as expected. | High | High | Pass |
| TC-06 | Todo | Update Todo | User owns a Todo | 1. Edit the Todo.<br>2. Save changes. | Todo is updated with the new values. | Works as expected. | High | High | Pass |
| TC-07 | Todo | Delete Todo | User owns a Todo | 1. Delete the Todo. | Todo is removed from the list. | Works as expected. | High | High | Pass |
| TC-08 | Todo | Toggle completed → incomplete | User owns a Todo | 1. Mark Todo as completed.<br>2. Mark it incomplete again.<br>3. Read the Todo again. | Todo remains incomplete after the update. | Completed state persists correctly. | High | High | Pass |
| TC-09 | Todo | Partial update keeps description | Todo has title and description | 1. Update only the title.<br>2. Read the Todo again. | Title changes and description stays unchanged. | Description is preserved. | High | High | Pass |
| TC-10 | Authorization | User B cannot read User A's Todo | User A owns a Todo | 1. Login as User B.<br>2. Request User A's Todo. | API returns `404 Not Found`. Todo data is not exposed. | API returns `404 Not Found`. | Critical | Critical | Pass |
| TC-11 | Authorization | User B cannot update User A's Todo | User A owns a Todo | 1. Login as User B.<br>2. Send an update request for User A's Todo. | API returns `404 Not Found`. Todo is not changed. | API returns `404 Not Found`; Todo is unchanged. | Critical | Critical | Pass |
| TC-12 | Authorization | User B cannot delete User A's Todo | User A owns a Todo | 1. Login as User B.<br>2. Send a delete request for User A's Todo. | API returns `404 Not Found`. Todo is not deleted. | API returns `404 Not Found`; Todo remains available. | Critical | Critical | Pass |
| TC-13 | Authorization | User B cannot see User A's Todo | User A and User B use separate sessions | 1. User A creates a Todo.<br>2. Login as User B in another session.<br>3. Open Todo list. | User B cannot see User A's Todo. | User A's Todo is not shown to User B. | Critical | Critical | Pass |
| TC-14 | Cache | Create Todo invalidates cache | User is logged in | 1. Create a Todo.<br>2. Check cache invalidation. | Todo list cache is invalidated. | Verified by automated test. | High | High | Pass |
| TC-15 | Cache | Update Todo invalidates cache | User owns a Todo | 1. Update the Todo.<br>2. Check cache invalidation. | Todo list cache is invalidated. | Verified by automated test. | High | High | Pass |
| TC-16 | Cache | Delete Todo invalidates cache | User owns a Todo | 1. Delete the Todo.<br>2. Check cache invalidation. | Todo list cache is invalidated. | Verified by automated test. | High | High | Pass |
| TC-17 | Frontend | Toggle handles API failure | Todo exists and update request fails | 1. Toggle the Todo.<br>2. Trigger an API failure. | Error is shown and UI does not keep an incorrect state. | Error toast is shown and UI state is restored. | High | Medium | Pass |
| TC-18 | E2E | Complete Todo journey | Application is running | Register → Login → Create Todo → Toggle → Verify → Logout | Complete flow works successfully. | Playwright test passed. | High | High | Pass |
| TC-19 | E2E | Cross-user isolation | Two browser contexts are available | User A creates Todo → User B logs in → Check Todo list. | User B cannot see User A's Todo. | Playwright test passed. | Critical | Critical | Pass |

---

## 4. Defect Tracking

### DEF-01 — Expired JWT Accepted

- **Severity:** Critical
- **Priority:** Critical
- **Status:** Fixed
- **Test Case:** TC-03

**Issue:**  
Expired access tokens were still accepted by the backend.

**Fix:**  
Removed the option that disabled JWT expiration validation.

**Result:**  
Expired tokens now return `401 Unauthorized`.

---

### DEF-02 — Partial Update Cleared Existing Description

- **Severity:** High
- **Priority:** High
- **Status:** Fixed
- **Test Case:** TC-09

**Issue:**  
Updating only the title could clear the existing description.

**Fix:**  
Changed the update data handling to use `exclude_unset=True`.

**Result:**  
Updating the title no longer removes the existing description.

---

### DEF-03 — Cross-User Todo Access

- **Severity:** Critical
- **Priority:** Critical
- **Status:** Fixed
- **Test Cases:** TC-10, TC-11, TC-12, TC-13

**Issue:**  
Todo access needed to be restricted to the authenticated user.

**Fix:**  
Todo queries and operations are restricted by the current user's ID.

**Result:**  
User B cannot read, update, delete, or see User A's Todo.

---

### DEF-04 — Todo Cache Was Not Invalidated

- **Severity:** High
- **Priority:** High
- **Status:** Fixed
- **Test Cases:** TC-14, TC-15, TC-16

**Issue:**  
Todo list cache could contain stale data after Todo mutations.

**Fix:**  
Invalidate the user's Todo list cache after create, update, and delete operations.

**Result:**  
Cache invalidation works correctly for all three operations.

---

### DEF-05 — Frontend Toggle Changed on API Failure

- **Severity:** Medium
- **Priority:** High
- **Status:** Fixed
- **Test Case:** TC-17

**Issue:**  
The Todo checkbox could change in the UI even when the update request failed.

**Fix:**  
Updated the frontend mutation handling to keep the UI state consistent with the API result.

**Result:**  
An error toast is shown and the incorrect UI state is not kept.

---

## 5. Automated Test Results

### Backend

Backend tests cover:

- Expired JWT rejection
- Cross-user authorization
- Completed `true → false` persistence
- Partial update behavior
- Redis cache invalidation

Run:

```bash
cd backend
python -m pytest tests/ -v
```

**Result:** All tests passed.

### Frontend

Playwright covers:

1. Register → Login → Create Todo → Toggle → Verify → Logout
2. Cross-user Todo isolation

Run:

```bash
cd frontend
npx playwright test
```

**Result:** 2 tests passed.

---

## 6. Test Summary

| Area | Result |
|---|---|
| Authentication | Pass |
| Todo CRUD | Pass |
| Todo State | Pass |
| Partial Update | Pass |
| Authorization | Pass |
| Cross-user Isolation | Pass |
| Cache Invalidation | Pass |
| Frontend Error Handling | Pass |
| E2E | Pass |

### Defect Summary

| Severity | Fixed | Remaining |
|---|---:|---:|
| Critical | 2 | 0 |
| High | 2 | 0 |
| Medium | 1 | 0 |
| **Total** | **5** | **0** |

---

## 7. Overall Result

**PASS**

All tested critical scenarios passed.

The identified issues were fixed and verified through backend tests, frontend E2E tests, and regression testing.

No unresolved Critical or High severity defects remain within the tested scope.