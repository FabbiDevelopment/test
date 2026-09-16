# Manual Test Plan — Authentication & Authorization

> Level 2C — Xác thực, ủy quyền, Todo CRUD, cache, tags (Level 4).

## Environment

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Start: `docker compose up -d`

## Test Matrix

| TC | Module | Scenario | Steps | Expected | Priority |
|----|--------|----------|-------|----------|----------|
| TC-01 | Auth | Login OK | Valid credentials | Redirect dashboard, token stored | P1 / High |
| TC-02 | Auth | Anti user enumeration | Wrong email vs wrong password | Both **401**, same message | P0 / Critical |
| TC-03 | Auth | Expired JWT rejected | Use expired token on `/todos` | **401** | P0 / Critical |
| TC-04 | Auth | Refresh token on protected route | Bearer refresh token | **401** invalid type | P0 / Critical |
| TC-05 | AuthZ | User A cannot GET User B todo | Cross-user ID | **403** | P0 / Critical |
| TC-06 | AuthZ | User A cannot PUT/DELETE B todo | Cross-user ID | **403** | P0 / Critical |
| TC-07 | Logic | completed true→false | Toggle checkbox off | Persisted `false` | P1 / Major |
| TC-08 | Logic | Partial update keeps description | PUT title only | Description unchanged | P1 / Major |
| TC-09 | Cache | Create/update/delete invalidates Redis | Mutate then GET list | Fresh data | P1 / Major |
| TC-10 | UI State | Logout clears React Query | Logout → login other user | No stale todos | P0 / Critical |
| TC-11 | Tags | Duplicate tag case-insensitive | Create "Work" then "work" | **409** | P2 / Major |
| TC-12 | Tags | Filter by tag_id | Attach tag, filter | Only tagged todos | P2 / Major |

## Severity Legend

- **Critical**: Security / data leak
- **High**: Core flow broken
- **Major**: Business logic wrong
- **Minor**: Cosmetic
