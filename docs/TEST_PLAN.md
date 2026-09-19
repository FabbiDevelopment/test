# Manual Test Plan

## Document control

| Field | Value |
|---|---|
| Scope/version | Current worktree based on `61b19fc` |
| Author | Nguyen Dinh Duc |
| Test window | `2026-09-18` – `2026-09-19`; automated remediation, required E2E journeys, and JWT endpoint matrix complete |
| Environment | macOS 26.6.2; Docker 29.5.2 / Compose 5.1.4; Compose application stack |
| Overall result | Backend/frontend regressions, six Playwright tests, Tier 3B infrastructure checks, and the JWT endpoint matrix pass |

## 1. Objective

Verify authentication, authorization, Todo CRUD, caching, frontend session isolation, infrastructure readiness, and optional Tier 4 behavior. This plan complements automated tests; it does not replace pytest, integration tests, or Playwright.

## 2. Scope

### In scope

- Registration, login, refresh, logout, and token rejection.
- User-to-user authorization boundaries.
- Todo create/read/update/delete and partial updates.
- Backend Redis cache isolation and invalidation.
- Frontend query/cache behavior across account changes.
- Docker cold-start and service health.
- Tag, filtering, and bulk-action behavior when Tier 4 is implemented.

### Out of scope

- Todo Sharing implementation; Tier 3A requires specification only.
- Third-party penetration testing.
- Production load testing outside the documented benchmark environment.

## 3. Test environment and prerequisites

| Component | Version/configuration | Status |
|---|---|---|
| Browser | Playwright 1.63.0 / Chromium 153.0.8010.12 | Suite 6/6 passes; both required Tier 2B journeys, Tier 4 UI journey, and dashboard pagination regression complete |
| Frontend | Host Node 24 / npm; Playwright Vite `http://127.0.0.1:4173` | Unit regressions 15/15, Playwright 6/6, lint, and production build pass |
| Backend | Non-root container Python 3.12; `http://localhost:8000` | Fast regression suite 49/49 plus PostgreSQL/Redis integration 3/3; Black and unfiltered Flake8 pass; backend health-gated cold start passes |
| PostgreSQL | Compose image `postgres:16-alpine` | Running; migration at head; 100 users and 1,000 todos seeded |
| Redis | Compose image `redis:7-alpine` | Healthy with password authentication; unauthenticated commands are rejected; Journey 1/2 real-cache paths pass |
| Docker | Docker 29.5.2 / Compose 5.1.4 | Four services healthy; readiness order, non-root app users, and internal-only data ports verified |
| OS | macOS 26.6.2 (Build 25G83) | Ready |
| Commit | `61b19fc` | Documentation synchronized; automated remediation, Tier 4, browser journeys, dashboard pagination, and JWT endpoint-matrix verification executed |

Required test identities:

| Account | Purpose | Setup method |
|---|---|---|
| Journey 1 user | Registration/login and Todo lifecycle | `e2e-journey1-r{0..2}@example.com`; reset before each suite |
| User A | Owner of private Todo data | `e2e-journey2-a-r{0..2}@example.com`; isolated Journey 2 context |
| User B | Cross-user authorization checks | `e2e-journey2-b-r{0..2}@example.com`; isolated Journey 2 context |
| Pagination user | Dashboard page navigation | `e2e-pagination-r{0..2}@example.com`; creates 101 owned Todos; reset before each suite |
| Revoked/deleted user | Token lifecycle checks | Planned fixture; account not created |

Do not record real passwords or tokens in this document. Use disposable local test credentials supplied through test configuration.

## 4. Entry criteria

- [x] Target commit is identified.
- [x] Required services become healthy on a cold start without a manual restart.
- [x] Database migrations completed successfully at `e5f7a9b1c2d3 (head)`.
- [x] Test data resets deterministically through an exact email allowlist before headless/headed/UI runs.
- [x] Backend automated tests were executed after remediation: 49/49 passed.
- [x] The fast suite has no Pydantic class-`Config` deprecation warning.
- [x] PostgreSQL/Redis integration tests were executed after remediation: 3/3 passed.
- [x] The fast suite has no pytest-asyncio custom-event-loop deprecation warning.
- [x] Backend Black and unfiltered Flake8 gates pass on the remediated tree.
- [x] Frontend unit regressions were executed: 15/15 passed.
- [x] Frontend lint and production build pass without the bundle-size (`FE-007`) or planned native config-loader (`FE-010`) warnings.
- [x] Frontend production and full dependency audits report 0 vulnerabilities.
- [x] Playwright Chromium suite passes 6/6, including both required Tier 2B journeys, the Tier 4 UI journey, and dashboard pagination.
- [x] No production credentials or data are used in assessment verification; tracked values are development placeholders.

## 5. Exit criteria

- [ ] All Critical and High cases pass.
- [ ] No cross-user data is visible in API, UI, logs, or caches.
- [ ] Failed cases have linked defects in `docs/BUG_REPORT.md`.
- [x] Actual Result and Status are filled for every executed case; executor and date are recorded in the execution log.
- [x] Retest and regression results are recorded after fixes.

## 6. Test case matrix

### Execution provenance

The executor and date for each automated, E2E, and integration evidence set are
recorded by Run ID in section 7. All current-worktree runs in this plan were
executed by Nguyen Dinh Duc with Codex assistance; RUN-034 is the final JWT
endpoint-matrix evidence.

| ID | Area | Scenario | Preconditions | Steps | Expected result | Priority / Severity | Actual result | Status |
|---|---|---|---|---|---|---|---|---|
| AUTH-01 | Registration | Register a new valid user | Email is unused | Submit valid registration form | User is created and valid tokens/session are returned | High / Major | Journey 1 receives 201, reaches the dashboard, and displays the registered email | Pass (E2E) |
| AUTH-02 | Registration | Register duplicate email concurrently | Email is unused; two clients ready | Submit two registrations at the same time | Exactly one user is created; the other request gets a stable conflict response | High / Critical | Database regression proves the unique constraint rejects duplicate inserts; route catches the resulting `IntegrityError` as a stable 400 | Pass (Automated) |
| AUTH-03 | Login | Invalid email and invalid password do not enumerate users | One known user | Try unknown email, then known email with wrong password | Both produce the same public status/message | High / Security | `test_login_failure_does_not_reveal_whether_email_exists` confirms identical 401 response bodies | Pass (Automated) |
| AUTH-04 | JWT | Expired access token is rejected | Expired token available | Call `/auth/me` and `/todos` | Both return 401 without protected data | High / Critical | `test_expired_access_token_is_rejected` returns 401 from both protected endpoints | Pass (Automated) |
| AUTH-05 | JWT | Tampered token is rejected | Valid token available | Modify payload/signature and call protected API | Request returns 401 | High / Critical | `test_tampered_access_token_is_rejected` alters the signature and receives 401 from both `/auth/me` and `/todos` | Pass (Automated) |
| AUTH-06 | JWT | Refresh token cannot act as access token | Valid refresh token | Call protected Todo endpoint with refresh token | Request returns 401 | High / Critical | `test_refresh_token_cannot_authenticate_access_endpoint` returns 401 from both `/auth/me` and `/todos` | Pass (Automated) |
| AUTH-07 | Refresh | Refresh token rotates once | Valid refresh token | Refresh, then reuse old token | New pair is issued; old refresh token is rejected | High / Critical | `test_refresh_token_rotation_rejects_replay` verifies the old token returns 401 after rotation | Pass (Automated) |
| AUTH-08 | Logout | Logout revokes the session | Logged-in user | Logout, then try `/auth/me` and refresh | Access and refresh token are rejected | High / Critical | `test_logout_revokes_access_and_refresh_session` verifies both requests return 401 after logout | Pass (Automated) |
| AUTH-09 | Login | Registered user can log in with valid credentials | Journey 1 account exists and is logged out | Submit the registered email/password | Login returns 200 and the dashboard displays the account | High / Major | Journey 1 logs out after registration, logs back in, and reaches the authenticated dashboard | Pass (E2E) |
| AUTH-10 | Validation | Registration and login reject empty or too-short passwords | Authentication endpoints available | Submit empty and 5-character passwords to both endpoints | Each request returns 422 before authentication logic or bcrypt | Medium / Major | Parameterized API regression covers both endpoints and both invalid lengths | Pass (Automated) |
| CONFIG-01 | CORS and logs | API accepts only configured browser origins and does not echo SQL by default | Default test settings | Send preflight from allowed and untrusted origins; inspect settings | Only configured origin receives CORS header; wildcard configuration fails; `DB_ECHO` is false | High / Security | API/config regressions cover allowed/rejected origins, wildcard rejection, and the false default | Pass (Automated) |
| TODO-01 | CRUD | Owner completes full Todo lifecycle | User A logged in | Create, read, update, complete by clicking its name, delete a Todo | Every operation succeeds and final read is 404 | High / Major | Journey 1 creates, edits, completes by clicking the Todo name, and deletes through the UI; a final authenticated GET returns 404 | Pass (E2E) |
| TODO-02 | Authorization | User B cannot read User A's Todo | User A owns Todo X; User B logged in | B requests `GET /todos/X` | 404 without data disclosure | High / Critical | API regression and Journey 2 confirm GET returns 404; B's list/UI omit X | Pass (Automated + E2E) |
| TODO-03 | Authorization | User B cannot update User A's Todo | Same as above | B updates X | 404; Todo remains unchanged | High / Critical | API regression and Journey 2 confirm PUT returns 404; owner title, description, and completion remain unchanged | Pass (Automated + E2E) |
| TODO-04 | Authorization | User B cannot delete User A's Todo | Same as above | B deletes X | 404; Todo still exists for A | High / Critical | API regression and Journey 2 confirm DELETE returns 404; owner can still retrieve and view X | Pass (Automated + E2E) |
| TODO-05 | Update | Toggle completed from true to false | Todo is completed | Submit `completed=false`, reload Todo | Persisted value is false | High / Major | API regression confirms response and subsequent GET persist `false` | Pass (Automated) |
| TODO-06 | Update | Partial title update preserves description | Todo has title and description | Update only title, then reload | Description is unchanged | High / Major | API regression confirms response and subsequent GET preserve description | Pass (Automated) |
| TODO-07 | Pagination | Pagination is bounded and deterministic | Multiple Todos, including equal timestamps | Request sequential pages and `size=101` | Stable order, no duplicates/omissions, oversized request rejected | Medium / Major | API regression rejects `size=101`; Playwright creates 101 Todos and confirms the 101st item is available on page 2 | Pass (Automated + E2E) |
| CACHE-01 | Isolation | User cache entries are isolated | A and B own different Todos | A loads list, then B loads list | B sees only B's data | High / Critical | Compose integration verifies distinct user-key namespaces in authenticated Redis; Journey 2 confirms B's real-Redis list response and UI exclude A's Todo | Pass (Integration) |
| CACHE-02 | Query scope | Pagination/filter changes cache identity | Cached list exists | Change page, size, filter, sort | Correct query-specific result is returned | High / Major | Query-key and backend regressions cover page/size plus keyword, status, Tag, and date inputs; Redis keys scope every list input | Pass (Automated + Integration) |
| CACHE-03 | Invalidation | Create/update/delete invalidates stale list | User has cached list | Perform each mutation, reload list | Latest committed data is returned immediately | High / Major | Compose integration confirms an update increments the real Redis version and returns fresh PostgreSQL state; Journey 1 covers full mutation lifecycle | Pass (Integration) |
| CACHE-04 | Transaction | Cache invalidation is commit-coordinated | Cache version and transaction boundary available | Force commit failure, then exercise a successful mutation boundary | Failed transaction rolls back without Redis change; successful path commits before Redis `incr` | High / Major | `test_failed_todo_commit_does_not_invalidate_cache` and `test_todo_cache_invalidation_follows_successful_commit` cover both paths | Pass (Automated) |
| CACHE-05 | Availability | Redis invalidation failure does not fail a committed mutation | Redis mock raises `RedisError` from `incr` | Create a Todo and reload its list | Create returns 201, data is DB-visible, and `todo_cache_invalidation_failed` is logged | High / Major | `test_create_todo_succeeds_when_cache_invalidation_is_unavailable` | Pass (Automated) |
| FE-01 | Session | Logout clears user-scoped client data | User A has loaded Todos | Logout; log in as B | No A data flashes or remains in cache/UI | High / Critical | Unit regression and Journey 1 logout pass; Journey 2 confirms separate-session isolation, while same-context A-to-B switching remains unit-only | Partial (Unit + E2E) |
| FE-02 | Error UX | Invalid login shows error without hard reload | Login page open | Submit wrong credentials | Stable error is shown; form remains usable | Medium / Major | Node regression confirms the global 401 handler leaves `/auth/login` responses for the form, while it still clears sessions for protected requests | Pass (Unit) |
| FE-03 | Bulk UX | Failed bulk status update reports safely | Simulate bulk API failure | Select Todos and submit a status action | Cached lists are not invalidated and a useful error is shown | Medium / Major | Node regression verifies the bulk failure handler leaves cache work untouched and reports the API message | Pass (Unit) |
| FE-04 | Query isolation | Todo query identity includes account, pagination, and filters | Query key factory available | Compare keys for different users, pages, sizes, keyword, status, Tag, and dates | Every response-changing input produces a distinct key | High / Critical | Node unit regression confirms distinct keys for every API list input | Pass (Unit) |
| FE-05 | Pagination | Dashboard reaches later Todo pages | Authenticated user owns 101 Todos | Load the dashboard, select Next, then apply a filter from page 2 | Request uses the selected page; the 101st Todo is visible on page 2; applying filters returns to page 1 | Medium / Major | Unit regression checks the selected page/query key and controls; Playwright creates 101 Todos and verifies page 2 and filter reset | Pass (Unit + E2E) |
| FE-06 | React rendering | Todo rows have stable React keys | A Todo list with reordered or removed entries | Render Todo rows | Every row key is the stable Todo ID, not its array position | Low / Minor | Node regression verifies `TodoList` uses `todo.id` and rejects `index` keys | Pass (Unit) |
| INFRA-01 | Startup | Clean Docker cold start is dependable | Services stopped; environment configured | Run `docker compose up -d --build --wait` | Dependencies become healthy and backend starts without race failure | High / Major | Health order observed: PostgreSQL/Redis → backend → frontend; all services healthy without restart | Pass (Integration) |
| INFRA-02 | Security | Runtime config isolates data services and app privileges | Compose rendered and running | Inspect config, ports, UIDs, and Redis auth | No published DB/cache port or tracked secret; apps non-root; Redis requires auth | High / Security | No DB/cache host bindings; tracked `.env` removed; UIDs 999/1000; unauthenticated Redis returns `NOAUTH` | Pass (Integration) |
| TAG-01 | Tier 4 | Duplicate tag names ignore casing per user | Tag schema migrated; two users exist | Create `Work`, then `work` through the API; create `WORK` for another user | Same-user request returns 409; other user succeeds | Medium / Major | `test_tag_crud_is_owner_scoped_and_invalidates_todo_cache` plus database constraint regression | Pass (Automated API + DB) |
| TAG-02 | Tier 4 | Cross-user tag attach is rejected | A owns Todo; B owns Tag | Attempt cross-user attachment and detach | Requests return 404; no foreign relation is created or removed | High / Critical | `test_todo_tag_mapping_is_owner_scoped_and_invalidates_cached_lists` | Pass (Automated API) |
| FILTER-01 | Tier 4 | Combined filters return correct stable page | Tagged Todos across dates/statuses | Apply tag, status, keyword, date, and page-size inputs | Only matching Todos and correct totals are returned; foreign tag filter is 404 | Medium / Major | `test_todo_filters_use_all_inputs_and_require_an_owned_tag` | Pass (Automated API) |
| BULK-01 | Tier 4 | Bulk status update is owner-scoped and atomic | Payload includes owned and foreign IDs | Submit bulk update | Mixed ownership returns 404 without changing owned Todos; all-owned request updates once | High / Critical | `test_bulk_status_update_is_atomic_owner_scoped_and_invalidates_cache` | Pass (Automated API) |
| FE-TAG-01 | Tier 4 frontend | Tag controls validate and refresh UI state | Authenticated dashboard; Tag API available | Create, rename, and delete a Tag; attach it to a Todo, then inspect filter choices | Blank/over-50 name and over-20 color are rejected locally; attach/detach refresh Todo queries and the attached badge | Medium / Major | Frontend `tagSchema`, Todo Tag mutation invalidation, and Tier 4 Playwright UI journey | Pass (Unit + E2E) |
| FE-FILTER-01 | Tier 4 frontend | Filter and bulk controls preserve query/cache boundaries | Authenticated dashboard with Todos and Tags | Apply/clear filters; select visible Todos; mark completed or active | Request has every selected filter; clear restores defaults; bulk mutation refreshes user-scoped Todo lists | High / Major | Query-key unit regression, React Query hooks, and Playwright baseline journeys | Pass (Unit + E2E) |

Add cases for every new finding or acceptance criterion. Keep test IDs stable across executions.

## 7. Execution log

| Run ID | Date/time | Commit | Environment | Executor | Scope | Result | Evidence |
|---|---|---|---|---|---|---|---|
| RUN-001 | `2026-09-18` | `c92fd72` | Local macOS / Python 3.14.7 | Nguyen Dinh Duc with Codex assistance | Backend automated-test baseline | Blocked before collection: `pytest` is not installed | Command output: `No module named pytest` |
| RUN-002 | `2026-09-18 12:13 +07:00` | `3d1936b` | Docker Compose 5.1.4 | Nguyen Dinh Duc with Codex assistance | Compose validation and cold start | **Fail**: config valid and images build, but backend exits before PostgreSQL is ready; manual restart succeeds | Backend log: `ConnectionRefusedError` to PostgreSQL; `INFRA-001` |
| RUN-003 | `2026-09-18 12:15 +07:00` | `3d1936b` | Backend container / Python 3.12 | Nguyen Dinh Duc with Codex assistance | Pytest regression baseline | **Pass with warnings**: 9/9 passed in 1.86s; 3 compatibility/deprecation warning groups | `TEST-003`, `CONFIG-001`, `DEP-002` |
| RUN-004 | `2026-09-18 12:15 +07:00` | `3d1936b` | Backend container | Nguyen Dinh Duc with Codex assistance | Black, Flake8, dependency consistency | **Fail**: Black 1 file; Flake8 5 × `E402`; `pip check` passes | `QUALITY-001`; `No broken requirements found` |
| RUN-005 | `2026-09-18 12:16 +07:00` | `3d1936b` | Host Node 24.17.0 / npm 11.13.0 | Nguyen Dinh Duc with Codex assistance | Frontend install, lint, build | **Pass with warning**: `npm ci`, lint and build pass; main JS is 521.24 kB | `FE-007` |
| RUN-006 | `2026-09-18 12:17 +07:00` | `3d1936b` | Host npm audit | Nguyen Dinh Duc with Codex assistance | Frontend dependency security | **Fail**: production audit reports 6 vulnerabilities (5 High, 1 Moderate); full tree reports 9 | `DEP-001` |
| RUN-007 | `2026-09-18 12:20 +07:00` | `3d1936b` | PostgreSQL 16 / Redis 7 / Compose stack | Nguyen Dinh Duc with Codex assistance | Migration, health, seed, runtime smoke | **Pass with warning**: migration at head, DB/Redis/HTTP healthy, 100 users and 1,000 todos seeded; password hash emits passlib/bcrypt error log | `DEP-002`; direct DB counts `users=100`, `todos=1000` |
| RUN-008 | `2026-09-18 12:20 +07:00` | `3d1936b` | Compose containers | Nguyen Dinh Duc with Codex assistance | Container privilege and exposed-port check | **Fail**: backend/frontend run as root; PostgreSQL/Redis published on all host interfaces | `INFRA-003`, `INFRA-004` |
| RUN-009 | `2026-09-18` | `5816658` | Isolated host Python 3.13.12 / SQLite / stateful Redis mock | Nguyen Dinh Duc with Codex assistance | Full backend remediation regression | **Pass with warnings**: 19/19 passed; Pydantic config and custom event-loop warnings remain | AUTH-001/002, TODO-001/002/003, CACHE-001/002 |
| RUN-010 | `2026-09-18` | `d5fa690` | Host Node 24.17.0 / npm 11.13.0 | Nguyen Dinh Duc with Codex assistance | Frontend unit regression, lint, and production build | **Pass with warning**: 2/2 tests, ESLint pass, build pass; bundle remains 521.44 kB | FE-001/002/003; `FE-007` |
| RUN-011 | `2026-09-18` | `24bba4d` | Isolated Python 3.12.12 / SQLite / stateful Redis mock; Node 24.17.0 / npm 11.13.0 | Nguyen Dinh Duc with Codex assistance | Full backend and frontend quality-gate rerun | **Pass with warnings**: backend 19/19, Black and unfiltered Flake8 pass; frontend 2/2, ESLint and build pass; 3 backend deprecation warnings and the 521.44 kB bundle warning remain | `QUALITY-001` verified; `TEST-003`, `CONFIG-001`, `DEP-002`, and `FE-007` remained open at this historical run |
| RUN-012 | `2026-09-18` | `33bac3f` | Node 24.17.0 / npm 11.13.0 / Playwright 1.63.0 / Chromium 153.0.8010.12 | Nguyen Dinh Duc with Codex assistance | Playwright installation/configuration and frontend regression | **Pass with warning**: Chromium smoke 1/1, unit tests 2/2, ESLint and build pass; bundle remains 521.44 kB | Browser setup verified; complete user journey and cross-user isolation scenarios remained pending at this historical run |
| RUN-013 | `2026-09-18` | `92d83dd` | Playwright 1.63.0 / Chromium 153.0.8010.12 / Vite 4173 / current Docker backend, PostgreSQL, and Redis | Nguyen Dinh Duc with Codex assistance | Lifecycle Journey 1 plus frontend regression | **Pass with warnings**: Playwright 2/2, unit tests 2/2, ESLint and build pass; dialogs emit accessibility warnings and bundle is 521.53 kB | Register → logout/login → create → edit → complete → delete → GET 404 → logout; Journey 2 remained pending at this historical run |
| RUN-014 | `2026-09-18` | `f214cc0` | Playwright 1.63.0 / Chromium 153.0.8010.12 / Vite 4173 / current Docker backend, PostgreSQL, and Redis | Nguyen Dinh Duc with Codex assistance | Cross-user Journey 2 and full frontend regression | **Pass with warnings**: Playwright 3/3 in 11.8s using 3 workers, unit tests 2/2, ESLint and build pass; dialog and bundle warnings remain | B list/UI excludes A's Todo; B GET/PUT/DELETE return 404; A's Todo remains unchanged; Tier 2B complete |
| RUN-015 | `2026-09-18` | `cba9e0d` | Docker backend/PostgreSQL/Redis; Playwright 1.63.0 / Chromium 153.0.8010.12 / Vite 4173 | Nguyen Dinh Duc with Codex assistance | Deterministic reset and headless/headed commands | **Pass with warnings**: two consecutive headless runs pass 3/3; second reset deletes 3 previous fixture users; headed `--list` resets them again and lists all 3 tests | Exact 9-email allowlist covers attempt/retries 0–2; reset requires `E2E_ALLOW_RESET=1`; dialog warnings remained at this historical run |
| RUN-016 | `2026-09-18` | `de88674` | Docker 29.5.2 / Compose 5.1.4; Python 3.12.14; Node 20 image | Nguyen Dinh Duc with Codex assistance | Tier 3B build, cold start, privilege, network/auth, and regression checks | **Pass with warnings**: all services healthy in dependency order; non-root UIDs; internal-only DB/cache ports; Redis rejects no-auth; backend 22/22, Black/Flake8, frontend 2/2/lint/build pass; existing bundle/deprecation warnings remain | `AUTH-005`, `INFRA-001`–`INFRA-005` verified; first container pytest exposed and led to fixing working-directory/cache ownership |
| RUN-017 | `2026-09-18` | `cb13a34` | PostgreSQL 16.15 / Docker Desktop; 10 CPUs / ~7.75 GiB; isolated `fabbi_performance` database | Nguyen Dinh Duc with Codex assistance | Tier 3C baseline/index/retest and backend regression | **Pass with warnings**: 10k users/1M Todos; Q1 median 22.245→0.056 ms and Q2 20.471→0.064 ms; migration concurrent upgrade/downgrade/re-upgrade passes; backend 23/23, Black, Flake8 pass; existing deprecation warnings remain | Raw plans, all timing samples, index size, migration safety, and limitations in `docs/PERFORMANCE_REPORT.md`; `DB-003` was fixed later in `457853c` |
| RUN-018 | `2026-09-18` | `576e7c6` | Fresh non-root Docker Python 3.12.14 image; Redis 7 Compose service | Nguyen Dinh Duc with Codex assistance | Refresh rotation, logout revocation, full backend quality gates, and real-Redis Lua smoke | **Pass with warnings**: 25/25 pytest, Black, and Flake8 pass; Redis proves one-time rotation and rejects refresh after logout; 3 known deprecation warnings remain | `test_refresh_token_rotation_rejects_replay`; `test_logout_revokes_access_and_refresh_session`; AUTH-003 verified |
| RUN-019 | `2026-09-18` | `6a68c70` | Fresh non-root Docker Python 3.12.14 image; PostgreSQL 16 and authenticated Redis 7 Compose services | Nguyen Dinh Duc with Codex assistance | Dedicated production-fidelity integration suite | **Pass with warnings**: 2/2 integration tests, Black across 33 files, Flake8 across app/fast/integration tests, and fast suite 31/31 pass; Pydantic, passlib, pytest-asyncio, and Redis-close deprecation warnings remain | Cache namespaces are distinct per user, mutation versioning refreshes PostgreSQL state, and two simultaneous refreshes yield exactly one 200 and one 401 |
| RUN-020 | `2026-09-18` | `3326159` | Fresh non-root Docker Python 3.12.14 image | Nguyen Dinh Duc with Codex assistance | pytest-asyncio event-loop maintenance | **Pass with warnings**: fast suite 31/31, Black across 33 files, and Flake8 across app/fast/integration tests pass; the custom-event-loop warning is absent, while Pydantic and passlib dependency warnings remain | Async tests explicitly use the supported session loop scope; pytest config turns a reintroduced custom `event_loop` fixture warning into an error |
| RUN-021 | `2026-09-18` | `dd80d33` | Fresh non-root Docker Python 3.12.14 image | Nguyen Dinh Duc with Codex assistance | Pydantic v2 settings migration | **Pass with warning**: fast suite 32/32, Black across 33 files, and Flake8 across app/fast/integration tests pass; only passlib/crypt dependency warning remains | `SettingsConfigDict` preserves required settings, `.env` lookup, and case sensitivity; Pydantic class-`Config` warning is absent |
| RUN-022 | `2026-09-18` | `15426ca` | Host Node 24.17.0 / npm 11.13.0 | Nguyen Dinh Duc with Codex assistance | Frontend dependency security remediation | **Pass with warnings**: clean `npm ci`, production and full `npm audit` both report 0 vulnerabilities; unit tests 5/5, ESLint, production build, and Playwright 3/3 pass | Axios 1.20.0, React Router DOM 7.18.4, and compatible transitive fixes are locked; build adds a Vite planned-native-config-loader warning tracked as `FE-010` |
| RUN-023 | `2026-09-19` | `fecd7e0` | Fresh non-root Docker Python 3.12 image | Nguyen Dinh Duc with Codex assistance | bcrypt compatibility remediation | **Pass**: pytest 34/34, Black (33 files), and Flake8 pass with no warnings | Removes Passlib's incompatible bcrypt-version lookup; regression covers an existing `$2b$` hash, a newly generated hash, and pre-validation of passwords above 72 UTF-8 bytes |
| RUN-024 | `2026-09-19` | `9b5c9f6` | Host Node 24 / npm; Docker backend/PostgreSQL/Redis; Chromium | Nguyen Dinh Duc with Codex assistance | Route-level code splitting | **Pass**: unit tests 6/6, ESLint, production build, and Playwright 3/3 pass; no 500 kB chunk warning | Login, registration, and dashboard are lazy-loaded behind an accessible loading state. Entry JS falls from 527.53 kB (164.96 kB gzip) to 293.00 kB (91.73 kB gzip); dashboard is a 54.11 kB (18.31 kB gzip) route chunk. Existing FE-008 dialog and FE-010 config-loader warnings remained tracked. |
| RUN-025 | `2026-09-19` | `b4242a0` | Host Node 24 / npm; Docker backend/PostgreSQL/Redis; Chromium | Nguyen Dinh Duc with Codex assistance | Todo-dialog accessibility description | **Pass**: unit tests 7/7, ESLint, production build, and Playwright 3/3 pass | Create and edit Todo dialogs expose a contextual description to screen readers. Playwright exercised both dialogs and emitted no Radix missing-description warning; FE-010 config-loader warning remained tracked. |
| RUN-026 | `2026-09-19` | `60c4a67` | Host Node 24 / npm; Docker backend/PostgreSQL/Redis; Chromium | Nguyen Dinh Duc with Codex assistance | Structured API error rendering | **Pass**: unit tests 8/8, ESLint, production build, and Playwright 4/4 pass | A FastAPI-style 422 `detail` array renders its validation message as toast text without a browser `pageerror`; unexpected error payloads use the form fallback rather than being rendered as React children. FE-010 config-loader warning remained tracked. |
| RUN-027 | `2026-09-19` | `259ab7f` | Host Node 24 / npm; Docker backend/PostgreSQL/Redis; Chromium | Nguyen Dinh Duc with Codex assistance | Vite native config-loader compatibility | **Pass**: unit tests 9/9, ESLint, production build, and Playwright 4/4 pass | Alias resolution uses `import.meta.dirname`; neither the planned-native-loader nor 500 kB chunk warning is emitted in build or the Playwright Vite server. |
| RUN-028 | `2026-09-19` | `85346dc` | Rebuilt Docker frontend at `http://localhost:3000`; Chromium | Nguyen Dinh Duc with Codex assistance | Stale frontend image remediation | **Pass**: frontend unit 9/9, ESLint, production build, and Docker-served Journey 1 1/1 pass | The browser's initial Todo-list request is asserted as `200` with `size=100`; the stale image previously sent `size=10000` and received `422`. |
| RUN-029 | `2026-09-19` | `3d7029d` | Fresh backend Docker image; host Node 24 / npm | Nguyen Dinh Duc with Codex assistance | Password-validation contract | **Pass**: backend pytest 38/38, Black, Flake8; frontend unit 10/10, ESLint, and production build pass | Empty and 5-character passwords return 422 from registration and login; Zod rejects passwords above 72 UTF-8 bytes. |
| RUN-030 | `2026-09-19` | `2d8bcff` | Fresh backend Docker image | Nguyen Dinh Duc with Codex assistance | CORS allowlist and SQL echo defaults | **Pass**: backend pytest 40/40, Black, and Flake8 pass | Configured `http://localhost:3000` is allowed; an untrusted origin receives no CORS allow-origin header; wildcard settings fail validation and SQL echo defaults to false. |
| RUN-031 | `2026-09-19` | CACHE-004 current worktree | Fresh backend Docker image | Nguyen Dinh Duc with Codex assistance | Redis-outage resilience for Todo mutations | **Pass**: backend pytest 41/41, Black, and Flake8 pass | A Redis `incr` failure after commit logs `todo_cache_invalidation_failed`; Todo creation still returns 201 and is DB-visible. |
| RUN-032 | `2026-09-19` | Tier 4 Tag DB current worktree | Fresh backend Docker image; disposable PostgreSQL 16 | Nguyen Dinh Duc with Codex assistance | Tag schema, indexes, and migration safety | **Pass**: backend pytest 44/44, Black, and Flake8; PostgreSQL upgrade → downgrade → re-upgrade passes | Case-insensitive per-user uniqueness, duplicate mapping rejection, and index metadata are covered. PostgreSQL exposes all expected Tag/mapping/filter indexes. |
| RUN-033 | `2026-09-19` | Tier 4 Tag API current worktree | Fresh backend Docker image; disposable PostgreSQL 16 and Redis 7 | Nguyen Dinh Duc with Codex assistance | Tag CRUD, mapping, filters, bulk transaction, and cache versioning | **Pass**: backend pytest 48/48; PostgreSQL/Redis integration 3/3 | API tests cover owner boundaries, all filter inputs, compatibility `page_size`, atomic bulk denial/success, and cache invalidation. Real Redis version increments after Tag/mapping/bulk mutations. |
| RUN-034 | `2026-09-19` | JWT matrix current worktree | Fresh backend Docker image / Python 3.12.14 | Nguyen Dinh Duc with Codex assistance | Expired, tampered, and refresh-token JWT rejection on `/auth/me` and `/todos` | **Pass**: pytest 49/49, Black, and Flake8 | Tampered-signature regression plus expanded expired/refresh regressions return 401 from both protected endpoints. |
| RUN-035 | `2026-09-19` | `61b19fc` | Docker backend/PostgreSQL/Redis; Playwright 1.63.0 / Chromium / Vite 4173 | Nguyen Dinh Duc with Codex assistance | Full E2E rerun at HEAD | **Pass**: Playwright 6/6 in 12.6s | Reset removed only five allowlisted fixture users and 103 fixture Todos; smoke, validation, lifecycle, cross-user, Tier 4, and pagination journeys all pass. |

## 8. Defect log

| Test case | Bug ID | Summary | Severity | Retest status |
|---|---|---|---|---|
| INFRA-01 | INFRA-001 | Backend loses the Compose cold-start race with PostgreSQL | High | Passed after healthchecks and readiness-aware dependencies |
| INFRA-02 | INFRA-002 | Development credentials are embedded in tracked Compose configuration | High | Passed after removing tracked `.env` files and requiring ignored environment config |
| INFRA-02 | INFRA-003 | PostgreSQL and unauthenticated Redis are published to the host | High | Passed after removing host ports and enabling Redis authentication |
| INFRA-02 | INFRA-004 | Backend and frontend containers run as root | Medium | Passed with non-root `app`/`node` users and scoped build contexts |
| AUTH-04 | AUTH-001 | Expired access tokens were accepted | Critical | Automated endpoint-matrix retest passed for `/auth/me` and `/todos` |
| AUTH-05 | AUTH-005 | A modified JWT signature must not authenticate protected routes | Critical | Automated endpoint-matrix regression passed for `/auth/me` and `/todos` |
| AUTH-06 | AUTH-002 | Refresh tokens could access protected endpoints | Critical | Automated endpoint-matrix retest passed for `/auth/me` and `/todos` |
| TODO-02/03/04 | TODO-001 | Todo item operations were not owner-scoped | Critical | Automated retest passed |
| TODO-05/06 | TODO-002/003 | Partial updates mishandled false and omitted fields | High | Automated retest passed |
| CACHE-01/02/03 | CACHE-001/002 | Cache leaked across users/queries and served stale mutations | Critical / High | Stateful-mock retest, Compose PostgreSQL/Redis integration, and real-Redis Journey 1/2 paths passed |
| CACHE-05 | CACHE-004 | Redis invalidation failure returned 500 after a committed Todo mutation | High | Automated outage-injection retest passes; the failure is logged while the write returns success |
| FE-01/04 | FE-001/002 | Client query identity and logout cleanup were not account-safe | High | Unit retest, Journey 1 logout, and Journey 2 isolated-session checks passed; same-context account switch remains unit-only |
| TODO-01 | FE-011 | Stale Docker frontend bundle requested `size=10000`, beyond backend limit | High | Rebuilt/recreated frontend image; Docker-served Journey 1 asserts the initial list request uses `size=100` and returns 200 |

## 9. Known limitations and residual risk

- Backend dependencies are not installed in the default system environment; the latest remediation run used isolated `uv --no-project` execution on Python 3.12.12, matching the project's Python 3.12 target without creating a project `uv.lock`.
- PostgreSQL and Redis are intentionally not reachable from the host through the default Compose file; host-run backend development requires separate local data services or an explicit local-only override.
- Seed data is suitable for local smoke/benchmark preparation but is randomly generated and is not a deterministic reset fixture.
- Both required Playwright journeys use fixed retry-indexed fixtures. The npm headless/headed/UI commands reset the exact allowlist before execution; concurrent suites against one backend are unsupported because they share that namespace.
- The fast backend suite intentionally uses SQLite and a Redis mock; it injects Redis failure for the post-commit Todo invalidation path, but the separately documented Compose integration suite remains required for PostgreSQL/Redis fidelity.

## 10. Approval

| Role | Name | Decision | Date | Notes |
|---|---|---|---|---|
| Execution owner | Nguyen Dinh Duc with Codex assistance | Completed | `2026-09-19` | Evidence is recorded in RUN-001–RUN-034; the final JWT matrix is RUN-034. |
| Author | Nguyen Dinh Duc | Test evidence acknowledged | `2026-09-19` | The plan records automated, E2E, integration, and JWT endpoint-matrix results; this is not a production release approval. |
| Independent reviewer | Not assigned | Not applicable | — | No external reviewer was designated for this assessment; no independent approval is claimed. |
