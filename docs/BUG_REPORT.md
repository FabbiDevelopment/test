# Bug Report and Issue Register

## Document control

| Field | Value |
|---|---|
| Assessment branch | `assessment/nguyen-dinh-duc` |
| Author | Nguyen Dinh Duc |
| Review date | `2026-09-19` |
| Application version/commit | `b89416b` (`test(auth): cover tampered JWT rejection and finalize test plan`) |
| Overall status | All recorded security, correctness, cache, infrastructure, and frontend findings are verified. Tier 4 Tags, filters, Todo-to-Tag mapping, bulk actions, cache invalidation, dashboard pagination, and their frontend controls are implemented end to end. |

## Purpose

This document is the source of truth for defects discovered during the assessment. Every finding must include a reproducible impact, a root cause, a scoped fix, and verification evidence. Update the status and evidence links in the same pull request that changes the behavior.

## Status definitions

| Status | Meaning |
|---|---|
| Open | Confirmed and not yet being fixed |
| In Progress | Implementation or verification is in progress |
| Fixed | Code change is complete but final evidence is pending |
| Verified | Regression and relevant integration tests pass |
| Deferred | Intentionally postponed with owner, reason, and risk acceptance |
| Rejected | Not reproducible or not a defect; include evidence |

No Critical or High issue may remain Deferred for final submission.

## Finding register

| ID | Area | Finding | Severity | Primary location | Status | Fix PR/commit | Verification |
|---|---|---|---|---|---|---|---|
| AUTH-001 | JWT | Expiration verification is disabled | Critical | `backend/app/core/security.py::verify_token` | Verified | `834bcf9` | `test_expired_access_token_is_rejected` returns 401 from `/auth/me` and `/todos`; current backend suite 49/49 passes |
| AUTH-002 | JWT | Access dependencies do not enforce token type | Critical | `backend/app/api/deps.py::get_current_user` | Verified | `834bcf9` | `test_refresh_token_cannot_authenticate_access_endpoint` rejects a refresh token on `/auth/me` and `/todos`; current backend suite 49/49 passes |
| AUTH-003 | Session | Refresh rotation/revocation and logout are ineffective | High | `backend/app/api/v1/auth.py`, `backend/app/core/redis.py` | Verified | `576e7c6` | `test_refresh_token_rotation_rejects_replay` and `test_logout_revokes_access_and_refresh_session`; fast Docker suite subsequently passes 38/38 |
| AUTH-004 | Authentication | Login response enables user enumeration | Medium | `backend/app/api/v1/auth.py::login` | Verified | `5771570` | `test_login_failure_does_not_reveal_whether_email_exists` verifies identical 401 body for unknown email and wrong password; fast Docker suite subsequently passes 38/38 |
| AUTH-005 | Configuration | Default JWT secret can be used outside a safe local profile | High | `backend/app/core/config.py` | Verified | `de88674` | Sensitive settings have no source fallback; three parameterized regressions require database, Redis, and JWT configuration |
| AUTH-006 | Validation | Authentication endpoints accept empty or too-short passwords | Medium | `backend/app/schemas/user.py`, `backend/app/api/v1/auth.py` | Verified | `3d7029d` | `UserCreate` and `UserLogin` require at least 6 characters and reject more than 72 UTF-8 bytes; API regressions cover empty/short registration and login requests. |
| TODO-001 | Authorization | Todo detail/update/delete are not owner-scoped | Critical | `backend/app/api/v1/todos.py` | Verified | `16cda47` | API regression and Playwright Journey 2 confirm cross-user GET/PUT/DELETE return 404 and owner data remains unchanged |
| TODO-002 | Update | `completed=false` is ignored | High | `backend/app/api/v1/todos.py::update_existing_todo` | Verified | `0ff4674` | `test_partial_update_can_set_completed_to_false`; backend suite 19/19 passes |
| TODO-003 | Update | An omitted description can be overwritten with `null` | High | `backend/app/api/v1/todos.py::update_existing_todo` | Verified | `0ff4674` | `test_partial_update_preserves_omitted_description`; backend suite 19/19 passes |
| CACHE-001 | Data isolation | Todo list cache key is shared across users and queries | Critical | `backend/app/api/v1/todos.py::list_todos` | Verified | `5816658` | Mock tests cover user/query variants; Journey 2 confirms user B's real-Redis list response and UI exclude user A's Todo |
| CACHE-002 | Consistency | Todo mutations do not invalidate list cache | High | `backend/app/api/v1/todos.py` | Verified | `5816658` | Mock regression passes; Playwright Journey 1 also observes fresh create/edit/complete/delete state against PostgreSQL and real Redis |
| CACHE-003 | Transactions | Cache invalidation is not coordinated with DB commit | High | `backend/app/api/v1/todos.py::commit_todo_mutation` | Verified | `b35b042` | Commit-order regressions prove failed commits leave Redis untouched and successful paths run `commit → invalidate`; fast Docker suite subsequently passes 38/38 |
| CACHE-004 | Availability | A Redis invalidation failure after DB commit makes a successful Todo mutation return 500 | High | `backend/app/api/v1/todos.py::commit_todo_mutation` | Verified | `08a2643` | `test_create_todo_succeeds_when_cache_invalidation_is_unavailable` proves the API returns 201, persists the Todo, and logs the invalidation failure; current backend suite 49/49 passes |
| DB-001 | Integrity | Email uniqueness is not enforced by the database | High | `backend/app/models/user.py`, `backend/alembic/versions/d4e6f8a0b2c3_add_users_email_unique_constraint.py` | Verified | `cc6bec5` | `test_user_email_is_unique_in_database` proves a duplicate insert raises `IntegrityError`; registration catches a concurrent constraint conflict; fast Docker suite subsequently passes 38/38 |
| DB-002 | Pagination | Todo queries have no deterministic ordering | Medium | `backend/app/services/todo_service.py::get_todos` | Verified | `cb13a34` | Newest-first `created_at, id` order and `test_get_todos_orders_newest_first`; 23/23 backend tests pass |
| DB-003 | Performance | Todo list performs an additional user query per row | Medium | `backend/app/services/todo_service.py::get_todos` | Verified | `457853c` | `test_todo_list_eager_loads_users_for_response` verifies every returned Todo has its user relationship eagerly loaded; fast Docker suite subsequently passes 38/38 |
| DB-004 | Performance | Core Todo queries lack a measured composite-index strategy | Medium | `todos` table migrations | Verified | `cb13a34` | PostgreSQL 16.15, 1M Todo before/after evidence in `docs/PERFORMANCE_REPORT.md`; Q1/Q2 medians improve 397.2×/322.4× |
| API-001 | Resource control | Todo page size has no upper bound | Medium | `backend/app/api/v1/todos.py::list_todos` | Verified | `729f1e8` | `test_todo_list_rejects_page_size_above_maximum` confirms `size=101` returns 422; backend cap and frontend default are both 100; fast Docker suite subsequently passes 38/38 |
| FE-001 | Data isolation | Todo React Query key omits user and pagination context | High | `frontend/src/features/todos/api/todos.ts` | Verified | `d5fa690` | Node regression confirms keys differ by user, page, and size; lint/build and the final 9/9 frontend unit suite pass |
| FE-002 | Session | Logout/account change does not clear user-scoped query data | High | Auth hooks and query client | Verified | `d5fa690` | Unit regression confirms token/query cleanup; Journey 1 confirms browser logout cleanup and Journey 2 confirms isolated sessions; same-context account switching remains unit-only |
| FE-003 | State | Optimistic update does not restore the snapshot on error | Medium | `frontend/src/features/todos/api/todos.ts` | Fixed | `d5fa690` | User-scoped snapshots are restored in `onError`; lint/build pass. A component-level forced-mutation-failure test is still a useful future strengthening. |
| FE-004 | Authentication | Global 401 handling reloads login and can hide form errors | Medium | `frontend/src/lib/api.ts` | Fixed | `773a960` | Node regression proves `/auth/login` 401 stays local to the form while protected-request 401 clears the session; unit tests, lint, and build pass |
| FE-005 | Pagination | Frontend requests 10,000 Todos by default | Medium | `frontend/src/features/todos/api/todos.ts::useTodos` | Fixed | `4a3f7fb` | Default page size is an explicit 100, matching the backend maximum; Node regression, lint, and build pass |
| FE-006 | React | Todo rows use array indexes as keys | Low | `frontend/src/features/todos/components/TodoList.tsx` | Verified | `b688c66` | Todo rows use stable Todo IDs; Node regression, lint, and build pass |
| INFRA-001 | Startup | Compose has no dependency healthchecks/readiness conditions | High | `docker-compose.yml` | Verified | `de88674` | Cold start with `docker compose up -d --build --wait` gates backend on healthy PostgreSQL/Redis and frontend on healthy backend; all four services become healthy |
| INFRA-002 | Secrets | Development credentials are embedded in tracked configuration | High | Compose, settings, tracked `.env` files | Verified | `de88674` | Tracked `.env` files removed; Compose requires database, Redis, and JWT values from ignored local environment configuration |
| INFRA-003 | Network | PostgreSQL and unauthenticated Redis are published to the host | High | `docker-compose.yml` | Verified | `de88674` | `docker compose ps` shows only internal `5432/tcp` and `6379/tcp`; unauthenticated `redis-cli ping` returns `NOAUTH` |
| INFRA-004 | Containers | Images run as root and lack scoped `.dockerignore` files | Medium | Backend/frontend Dockerfiles | Verified | `de88674` | Backend runs as `uid=999(app)`, frontend as `uid=1000(node)`; scoped ignore files reduce contexts to application inputs and exclude nested caches |
| INFRA-005 | Build | Frontend build is not reproducible and runtime Vite env is ineffective | Medium | Frontend Dockerfile and Compose | Verified | `de88674` | Image build uses `npm ci`; `VITE_API_URL` is supplied as a build argument; production image build passes |
| TEST-001 | Coverage | Existing tests cover happy paths but not security boundaries | High | `backend/tests/` | Verified | `cea96fd`, `5816658`, `576e7c6`–`b89416b` | Suite covers expiry, tampered signatures, token type, refresh rotation/revocation, login enumeration, password validation, database email/tag uniqueness, cross-user CRUD, cache isolation/invalidation/commit ordering/outage handling, Todo-to-Tag mapping integrity, eager Todo users, bounded pagination, partial updates, required secrets, stable ordering, settings, and CORS configuration; 49/49 pass |
| TEST-002 | Fidelity | SQLite and per-request Redis mocks do not validate production behavior | Medium | `backend/integration_tests/` | Verified | `6a68c70` | Dedicated Compose suite passes 2/2 against PostgreSQL 16 and authenticated Redis 7: direct user-scoped cache namespaces/invalidation plus atomic concurrent refresh rotation |
| TEST-003 | Test maintenance | Custom async event-loop fixture is deprecated and will become an error | Low | `backend/tests/`, `backend/pytest.ini` | Verified | `3326159` | Tests declare session loop scope with pytest-asyncio and a warning filter makes reintroducing the deprecated custom fixture fail; fast suite 38/38 has no pytest-asyncio event-loop warning |
| CONFIG-001 | Backend compatibility | Pydantic class-based `Config` is deprecated before Pydantic v3 | Low | `backend/app/core/config.py` | Verified | `dd80d33` | `SettingsConfigDict` preserves the environment-file and case-sensitive contract; configuration regression plus backend tests, Black, and Flake8 pass without the Pydantic warning |
| CONFIG-002 | Security | CORS permits any origin and SQL echo logs queries by default | High | `backend/app/main.py`, `backend/app/core/config.py` | Verified | `2d8bcff` | Credentialed CORS now uses configured non-wildcard origins; `DB_ECHO` defaults to `false`. Regressions cover allowed/rejected origins, CORS validation, and the logging default. |
| DEP-001 | Frontend security | Production dependency tree contains 6 known vulnerabilities | High | `frontend/package.json`, `frontend/package-lock.json` | Verified | `15426ca` | Axios floor raised to 1.20.0, React Router DOM floor to 7.18.4, and compatible transitive fixes are locked; `npm audit` reports 0 vulnerabilities |
| DEP-002 | Backend compatibility | Passlib/bcrypt stack emits an internal version lookup error during password hashing | Medium | `backend/requirements.txt`, `backend/app/core/security.py` | Verified | `fecd7e0` | Removed unmaintained Passlib and call bcrypt directly; current `$2b$` hashes remain valid. Registration/login reject passwords over bcrypt's 72 UTF-8-byte limit before hashing, and the backend suite has no Passlib/`crypt` warning. |
| QUALITY-001 | Backend quality | Required backend Black and Flake8 gates failed | Low | `backend/tests/conftest.py` | Verified | `24bba4d` | The five intentionally delayed imports document the database bootstrap requirement and use scoped `# noqa: E402`; `black --check .` and unfiltered `flake8 app tests` pass |
| FE-007 | Frontend performance | Production JavaScript bundle exceeds Vite's 500 kB warning threshold | Medium | `frontend/src/router/index.tsx` | Verified | `9b5c9f6` | Login, registration, and Todo dashboard pages load per route via `React.lazy`; the production build no longer emits Vite's 500 kB chunk warning. |
| FE-008 | Accessibility | Todo dialogs omit an accessible description | Low | `frontend/src/features/todos/components/TodoForm.tsx` | Verified | `b4242a0` | Create and edit Todo dialogs now render a contextual `DialogDescription`, associating the form purpose with the dialog for screen readers; Playwright no longer logs Radix's missing-description warning. |
| FE-009 | Error handling | Structured registration validation errors can crash React toast rendering | Medium | `frontend/src/lib/apiError.ts`, `frontend/src/features/auth/components/` | Verified | `60c4a67` | Axios error details are normalized to a non-empty string before reaching Sonner. FastAPI 422 arrays expose their first validation `msg`; unknown payloads use a safe form-specific fallback. |
| FE-010 | Build compatibility | Vite config uses `__dirname`, unsupported by the planned native config loader | Low | `frontend/vite.config.ts` | Verified | `259ab7f` | The alias now resolves from `import.meta.dirname`; Vite's production build succeeds without the planned-native-loader warning. |
| FE-011 | Runtime deployment | A stale frontend bundle requests an unsupported Todo page size | High | Running `frontend` image; `frontend/src/features/todos/api/queryKeys.ts` | Verified | `85346dc` | Rebuilt/recreated frontend image and Playwright Journey 1 against `http://localhost:3000` verifies the initial Todo request returns `200` with `size=100`. |
| DOC-001 | Deliverables | `docs/` was ignored despite required assessment documents | Medium | `.gitignore` | Verified | `3d1936b` | Deliverables are tracked while `docs/ANSWER_KEY.md` remains ignored |

Add newly discovered issues before implementing their fixes. Do not silently omit a finding because it falls outside the minimum five fixes required by Tier 1.

### AUTH-006 — Authentication accepts passwords shorter than the UI contract

- **Status:** Verified
- **Severity:** Medium
- **Category:** Validation / Authentication
- **Location:** `backend/app/schemas/user.py::UserCreate`,
  `backend/app/schemas/user.py::UserLogin`, and `backend/app/api/v1/auth.py::login`.
- **Observed behavior:** The backend only rejected passwords above bcrypt's
  72-byte limit. Empty and short values reached registration or login even though
  the frontend requires at least 6 characters.
- **Expected behavior:** Registration and login reject passwords shorter than 6
  characters with `422`; both layers also reject passwords exceeding 72 UTF-8
  bytes before bcrypt is called.
- **Fix applied:** Added Pydantic `min_length=6` to both authentication request
  schemas, changed the login route to use `UserLogin`, and reused a Zod password
  schema that enforces both the character minimum and byte maximum.
- **Regression test:** Backend parameterized API test covers empty and 5-character
  passwords for `/auth/register` and `/auth/login`. Frontend unit test covers a
  valid 6-character password and UTF-8 boundaries (18 vs. 19 emoji).
- **Verification:** The original remediation passed at 40/40; the current
  backend suite is 49/49 with Black and Flake8 passing, and the frontend suite
  is 15/15 with ESLint and production build passing.
- **PR/commit:** `3d7029d`.

### CACHE-004 — Redis invalidation failure turns a committed Todo mutation into 500

- **Status:** Verified
- **Severity:** High
- **Category:** Availability / Consistency
- **Location:** `backend/app/api/v1/todos.py::commit_todo_mutation`.
- **Observed behavior:** The helper committed the database transaction, then
  awaited Redis invalidation without handling Redis errors. A Redis outage could
  therefore return `500` after a Todo was already written, encouraging the
  client to retry and create a duplicate.
- **Expected behavior:** A database commit remains successful when cache
  invalidation is unavailable. The cache failure is observable, while DB commit
  failures still roll back and fail the request.
- **Fix applied:** Redis `RedisError` during Todo-list version invalidation is
  handled as best effort only after a successful commit. The application logs
  the `todo_cache_invalidation_failed` event with the affected user ID and a
  traceback for alerting.
- **Compatibility/tradeoffs:** This prioritizes write availability and avoids
  duplicate retries. If Redis recovers with an old list entry, that entry can
  remain stale for its five-minute TTL. A durable outbox or idempotency key is
  the next step if immediate invalidation or retry-safe write deduplication is
  required.
- **Regression test:** `test_create_todo_succeeds_when_cache_invalidation_is_unavailable`
  makes Redis `incr` fail, then verifies `201`, DB-visible data, and the warning
  event.
- **Verification:** The original remediation passed at 41/41; the current
  backend Docker suite is 49/49 with Black and Flake8 passing.
- **PR/commit:** `08a2643`.

### CONFIG-002 — Credentialed CORS is open and SQL logging defaults to on

- **Status:** Verified
- **Severity:** High
- **Category:** Configuration / Data exposure
- **Location:** `backend/app/main.py::CORSMiddleware` and
  `backend/app/core/config.py::Settings`.
- **Observed behavior:** CORS used `allow_origins=["*"]` while credentials were
  enabled, and SQLAlchemy echo was on by default. Any browser origin could make
  requests, and application logs could include query values such as email
  addresses.
- **Fix applied:** Added comma-separated `CORS_ORIGINS` configuration with
  normalization and wildcard rejection. The middleware accepts only that
  allowlist and required API methods/headers. `DB_ECHO` now defaults to `false`;
  Compose and `.env.example` expose both settings explicitly.
- **Regression test:** Configuration tests cover default values, multi-origin
  parsing, and wildcard rejection. API regression verifies the local frontend
  origin receives CORS headers while an untrusted origin does not.
- **Verification:** The original remediation passed at 40/40; the current
  backend Docker suite is 49/49 with Black and Flake8 passing.
- **PR/commit:** `2d8bcff`.

### FE-011 — Stale frontend image requests an invalid Todo page size

- **Status:** Verified
- **Severity:** High
- **Category:** Deployment / Availability
- **Location:** The running Compose `frontend` image; current source default is
  `frontend/src/features/todos/api/queryKeys.ts::DEFAULT_TODO_PAGE_SIZE`.
- **Requirement:** The frontend default must respect the backend
  `GET /api/v1/todos` limit of `1..100`.
- **Observed behavior:** After a successful login, the browser displays
  “Failed to load todos. Please try again.” The backend log records
  `GET /api/v1/todos?page=1&size=10000` followed by `422 Unprocessable Entity`.
- **Expected behavior:** The browser requests `size=100` (the current frontend
  default and backend maximum) and renders the Todo list or the empty state.
- **Impact:** A logged-in user cannot load Todos. The generic UI error hides the
  actionable server validation reason.
- **Reproduction:**
  1. Start the currently cached Compose frontend image and open
     `http://localhost:3000`.
  2. Log in with a valid account.
  3. Observe the Todo error UI and the backend request with `size=10000`.
  4. Compare with current source, where `DEFAULT_TODO_PAGE_SIZE` is `100`, or
     call the API with the same token and `size=100` to receive `200`.
- **Root cause:** The running frontend image was created at
  `2026-09-18T07:56:24Z`, before the bounded-page-size change, then restarted
  without rebuilding. It serves an obsolete Vite bundle while the backend is
  current and correctly rejects the old request contract.
- **Fix applied:** Rebuilt and recreated the frontend from the current commit:
  `docker compose up -d --build --force-recreate frontend`. Journey 1 now
  asserts the first browser Todo-list request has `size=100` and receives `200`,
  providing a served-application guard against this contract drift.
- **Compatibility/tradeoffs:** Rebuilding the static frontend is safe and does
  not alter data. It briefly restarts only the frontend service; active browser
  sessions need a refresh.
- **Regression test:** `frontend/e2e/todo-lifecycle.spec.ts` waits for the
  initial Todo-list response, requires `200`, and asserts `size=100`. The
  existing `frontend/tests/cache-isolation.test.ts` retains the source-level
  default check.
- **Integration/manual evidence:** `2026-09-19` local runtime: valid login and
  `GET /todos?page=1&size=100` return `200`; the stale bundle's request with
  `size=10000` returns `422`. After the targeted image rebuild, Playwright
  Journey 1 against Docker frontend passes 1/1 and verifies `size=100`.
- **PR/commit:** `85346dc`.

## Detailed finding template

Copy this section once per finding or link the register row to the corresponding heading.

### `<ID>` — `<short title>`

- **Status:** Open
- **Severity:** Critical / High / Medium / Low
- **Category:** Security / Correctness / Performance / Infrastructure / Testing / Documentation
- **Location:** `<file:function or line>`
- **Requirement:** `<README tier/task or internal invariant>`
- **Observed behavior:** `<what currently happens>`
- **Expected behavior:** `<safe/correct result>`
- **Impact:** `<confidentiality, integrity, availability, UX, performance>`
- **Reproduction:**
  1. `<precondition>`
  2. `<action>`
  3. `<observable result>`
- **Root cause:** `<technical cause>`
- **Fix proposal:** `<minimal root-cause fix>`
- **Compatibility/tradeoffs:** `<API, migration, performance, operational impact>`
- **Regression test:** `<test name/path>`
- **Integration/manual evidence:** `<command, result, log, screenshot, benchmark>`
- **PR/commit:** `<link or SHA>`
- **Reviewer notes:** `<notes>`

## README traceability matrix

| Requirement | Planned artefact/change | Evidence | Status |
|---|---|---|---|
| Tier 1: report impactful findings | This document and final PR description | Register contains location, severity, cause, fix and verification for every recorded finding | Complete; PR link remains an external submission task |
| Tier 1: at least five fixes, including two backend and one frontend | Finding register and implementation commits | AUTH-001/002, TODO-001/002/003, CACHE-001/002, FE-001/002/003 and later fixes | Complete |
| Tier 2A: at least three backend critical scenarios | `backend/tests/` | 49/49 pass, including expiry, tampered signatures, token type, ownership, password validation, partial-update, cache, Tag API/filter/bulk, rotation/revocation, configuration and dependency regressions | Complete |
| Tier 2B: two required Playwright scenarios | `frontend/e2e/` and `frontend/playwright.config.ts` | Lifecycle Journey 1 and cross-user isolation Journey 2 pass; smoke, structured-error, Tier 4, and pagination regressions bring the suite to 6/6 | Complete (2/2 required journeys) |
| Tier 2C: manual test plan | `docs/TEST_PLAN.md` | Structured matrix, execution history, JWT endpoint matrix, executor, and automated evidence are recorded | Complete |
| Tier 3A: Todo Sharing specification only | `docs/TODO_SHARING_SPEC.md` | Production-grade proposed specification with stories, schema, APIs, authorization, cache and rollout | Complete |
| Tier 3B: at least three infrastructure improvements | Compose/Docker changes | Healthy cold start; non-root UIDs; authenticated/internal-only data services; scoped build contexts | Complete (5 improvements) |
| Tier 3C: query analysis, migration, benchmark, tradeoffs | Migration and `docs/PERFORMANCE_REPORT.md` | PostgreSQL 16.15; 10k users/1M Todos; raw plans/timings; concurrent index migration and rollback evidence | Complete |
| Git workflow and PR submission | Atomic Conventional Commits and final PR | `<git log/PR>` | In Progress |
| AI disclosure | `docs/AI_USAGE.md` | Assistance log updated through pagination and JWT-matrix verification | Complete deliverable; candidate attestation remains pending |
| Tier 4 bonus | Tags, filters, bulk actions and tests | Tag/mapping schema, API, filters, bulk transaction, cache regressions, and frontend UI | Complete |

## Verification summary

| Check | Command/environment | Expected | Actual | Date | Evidence |
|---|---|---|---|---|---|
| Compose validation | `docker compose --env-file .env.example config -q` | Pass | Pass (exit 0) | `2026-09-18` | Required secret variables resolve from the documented template; rendered Compose is valid |
| Backend tests | `docker compose run --rm --no-deps --build backend sh -c 'pytest tests/ -v && black --check . && flake8 app tests'` | Pass | Pass in a fresh non-root Python 3.12 image: 49/49; Black and Flake8 pass | `2026-09-19` | Includes Tag CRUD ownership, cross-user mapping denial, filters, `page_size` compatibility, atomic bulk updates, cache invalidation, and expired/tampered/refresh JWT rejection on both protected endpoints |
| PostgreSQL/Redis integration tests | Disposable PostgreSQL 16 and authenticated Redis 7 containers; `alembic upgrade head && pytest integration_tests/ -q` | Pass | Pass: 3/3 | `2026-09-19` | Verifies cache key isolation/invalidation, concurrent refresh rotation, and real Redis version increases after Tag, mapping, and bulk mutations |
| Backend regression suite | `uv run --python 3.12 --isolated --no-project --with-requirements requirements.txt pytest tests/ -v` | Pass | Pass on Python 3.12.12: 19 collected, 19 passed; 3 deprecation warning groups | `2026-09-18` | Covers AUTH-001/002, TODO-001/002/003, CACHE-001/002; SQLite and stateful Redis mock only |
| Backend format/lint | `black --check .`; `flake8 app tests integration_tests` | Pass | Black passes for all 33 Python files; Flake8 completes without findings | `2026-09-18` | `QUALITY-001` verified after five documented, scoped `E402` suppressions |
| Backend dependencies | `docker compose exec -T backend pip check` | Pass | Pass: no broken requirements found | `2026-09-19` | The Passlib compatibility warning was removed by `DEP-002` |
| Frontend install | `cd frontend && npm ci` | Pass | Pass: 287 packages installed/audited | `2026-09-18` | Command exit 0 |
| Frontend lint | `cd frontend && npm run lint` | Pass | Pass (exit 0) | `2026-09-19` | ESLint completed without findings after Tier 4 frontend work |
| Frontend unit regression | `cd frontend && npm test` | Pass | Pass: 15/15 | `2026-09-19` | Query/session/401/page-size/row-key, dashboard pagination, one multi-select checkbox per Todo, full filter-key dimensions, Tag form/date validation, bulk success/failure cache handling, password limits, lazy routes, native Vite config, dialog description, and structured-error regressions |
| Frontend build | `cd frontend && npm run build` | Pass | Pass without the Vite 500 kB or planned-native-loader warnings; entry JS is 293.00 kB (91.72 kB gzip) | `2026-09-19` | Tier 4 frontend, `FE-007`, `FE-010` |
| Frontend dependency audit | `cd frontend && npm audit --omit=dev`; `npm audit` | No known vulnerabilities | Pass: 0 production and 0 total vulnerabilities | `2026-09-18` | `DEP-001`; compatible direct/transitive lockfile updates |
| Playwright | `cd frontend && npm run test:e2e` | Pass | Headless suite passes 6/6 at `61b19fc` in 12.6s | `2026-09-19` | Deterministic retry-indexed accounts, smoke, structured-error, Tier 4 Tag/filter/bulk, 101-Todo pagination, and both required journeys on Vite 4173 with Docker backend/PostgreSQL/Redis |
| Playwright headed command | `cd frontend && npm run test:e2e:headed -- --list` | List configured tests | Pass: reset removes the 3 remaining fixture users and Playwright lists 3 Chromium tests | `2026-09-18` | Validates the documented headed script without opening a GUI during automated verification |
| PostgreSQL/Redis smoke | `pg_isready`; `redis-cli ping`; README seed command | Pass | Pass: PostgreSQL accepts connections, Redis returns `PONG`, seed created 100 users and 1,000 todos | `2026-09-18` | Counts verified directly in PostgreSQL |
| Service HTTP smoke | `curl http://localhost:8000/health`; `curl -I http://localhost:3000` | Pass | Pass: backend reports healthy; frontend returns HTTP 200 | `2026-09-18` | Both app services also report healthy through Compose healthchecks |
| Docker cold start | `docker compose up -d --build --wait` | All services start reliably | Pass: PostgreSQL/Redis became healthy before backend; frontend started after backend became healthy | `2026-09-18` | `INFRA-001` verified without a manual restart |
| Migration upgrade/downgrade | `alembic upgrade head`; `alembic current` against PostgreSQL | Pass | Current head is `e5f7a9b1c2d3`; Tag migration upgrade → downgrade → re-upgrade passes, and performance-index rollback/reapply remains documented | `2026-09-19` | Email-uniqueness migration preflights duplicate data; concurrent-index rollback evidence is in `docs/PERFORMANCE_REPORT.md` |
| Container hardening | `docker compose exec -T {backend,frontend} id`; `docker compose ps`; Redis auth probes | Non-root; authenticated data services not host-published | Pass: app UIDs are 999/1000; DB/cache expose no host bindings; unauthenticated Redis returns `NOAUTH` and authenticated ping succeeds | `2026-09-18` | `INFRA-002`–`INFRA-005` verified |
| Performance benchmark | See `docs/PERFORMANCE_REPORT.md` | PostgreSQL evidence, migration, plans, timings, tradeoffs | Pass: 10k users/1M Todos; Q1 median 22.245→0.056 ms and Q2 20.471→0.064 ms; index is 56 MB; concurrent upgrade/downgrade/re-upgrade pass | `2026-09-18` | `DB-002`, `DB-004`; no SQLite evidence used |

## Residual risks and accepted limitations

| Risk | Severity | Reason not fixed | Mitigation | Owner | Review date |
|---|---|---|---|---|---|
| Redis invalidation is best effort, not durable | Medium | A Redis `incr` outage no longer fails a committed Todo mutation, but an old cached list can remain stale for its five-minute TTL after Redis recovers | Alert on `todo_cache_invalidation_failed`; add an outbox or idempotency key if immediate invalidation or write deduplication is required | Nguyen Dinh Duc | `2026-09-19` |
