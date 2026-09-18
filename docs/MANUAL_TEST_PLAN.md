# Manual Test Plan: Authentication and Todo Regression

## Environment

- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`
- Browser: current Chrome or Chromium
- Accounts: create User A and User B with distinct email addresses.

| ID | Scenario | Preconditions | Steps | Expected result | Priority / Severity | Status |
|---|---|---|---|---|---|---|
| AUTH-01 | Login succeeds | Registered account | Submit valid email and password | Redirect to Todo page and user email is shown | High / Major | Not run |
| AUTH-02 | Invalid credentials | Registered account | Submit a wrong password, then an unknown email | Both return the same generic error | High / Security | Not run |
| AUTH-03 | Expired token | Obtain an expired access token | Call `/api/v1/auth/me` | `401 Unauthorized` | High / Critical | Automated |
| AUTH-04 | Logout isolation | User A has loaded todos | Logout then log in as User B in the same browser | User A's todos and profile are absent | High / Security | Not run |
| TODO-01 | Toggle completion | User has a Todo | Toggle checked to unchecked; reload; toggle back; reload | Each state persists | High / Major | Automated |
| TODO-02 | Partial update | Todo has a description | Edit title only | Description stays unchanged | High / Major | Automated |
| TODO-03 | Cross-user access | User B owns a Todo | User A calls GET, PUT, DELETE using B's Todo ID | Each request returns `404`; B's Todo remains unchanged | High / Critical | Automated |
| TODO-04 | Cache after create/update/delete | Todo list has been loaded | Create, edit, and delete a Todo; reload after each action | List reflects the newest state without stale items | High / Major | Not run |
| TODO-05 | Ordering | User has several Todos | Reload after creating a Todo | Newest Todo remains first; order is stable | Medium / Major | Automated |

## Defect recording

Record browser, timestamp, request ID, reproducible steps, observed result, expected result, severity, and evidence for any failed case.
