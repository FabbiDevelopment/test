# AI Assistance Disclosure

## Document control

| Field | Value |
|---|---|
| Candidate | Nguyen Dinh Duc |
| Assessment branch | `assessment/nguyen-dinh-duc` |
| Covered period | `2026-09-18` – `2026-09-19` |
| Last updated | `2026-09-19` |
| Status | In Progress |

## 1. Disclosure statement

AI-assisted tools are being used during this assessment for repository analysis, risk prioritization, planning, and documentation scaffolding. Generated suggestions are treated as drafts until reviewed against the repository, README requirements, tests, and runtime behavior. The candidate remains responsible for every submitted change and decision.

## 2. Tools used

| Tool/model | Purpose | Access level | Data shared | Human verification |
|---|---|---|---|---|
| OpenAI Codex | Repository review, security/correctness analysis, assessment planning, and Markdown drafting | Read/write access to the assessment workspace | Repository source, configuration, Git metadata, and user-provided prompts; no production data or credentials | Compared with `README.md`, source code, Git state, and local static checks; candidate review remains required |

## 3. Assistance log

Record material assistance, not every autocomplete event. Group closely related prompts when appropriate.

| ID | Date | Task | Prompt summary or sanitized prompt | Files/areas affected | Output used | Verification |
|---|---|---|---|---|---|---|
| AI-001 | `2026-09-18` | Repository analysis | Review the complete project structure and identify suspicious or unsafe behavior | Backend, frontend, Docker, dependencies, Git history | Accepted as an initial audit; findings remain Open until reproduced | Static source/config review and Git inspection |
| AI-002 | `2026-09-18` | Agent guidance | Read the project and create repository-specific instructions | `AGENTS.md` | Draft accepted into the worktree | Compared with README, GUIDE, source layout, and tool configuration |
| AI-003 | `2026-09-18` | Remediation planning | Create and expand a senior-level remediation sequence covering all mandatory and bonus requirements | `REMEDIATION_PLAN.md` | Draft accepted into the worktree | Cross-checked against every README tier and Git rule |
| AI-004 | `2026-09-18` | Requirements analysis | Re-read README and extract mandatory, optional, scoring, branch, commit, and submission rules | `README.md`, planning documents | Used to update the plan and guidance | Direct line-by-line README review |
| AI-005 | `2026-09-18` | Documentation scaffolding | Create assessment templates for findings, manual tests, Todo Sharing, performance evidence, and AI disclosure | `.gitignore`, `docs/*.md` | Accepted as draft templates | Ignore behavior and Markdown structure checked locally |
| AI-006 | `2026-09-18` | Initial metadata | Populate verifiable branch, commit, environment, test-blocker, and assistance information | `docs/BUG_REPORT.md`, `docs/TEST_PLAN.md`, `docs/AI_USAGE.md` | Accepted as initial data; candidate identity spelling/sign-off must be confirmed | Git metadata and local tool versions queried directly |
| AI-007 | `2026-09-18` | Backend regression coverage | Add API regressions for JWT expiry/type, Todo ownership, cache isolation/invalidation, and partial updates | `backend/tests/` | Tests accepted and committed | Baseline failures reproduced; final backend suite passes 19/19 |
| AI-008 | `2026-09-18` | Backend remediation | Fix JWT validation, owner-scoped Todo access, partial updates, and versioned user/query cache behavior | Backend security, dependencies, Todo routes/services, Redis wrapper | Changes accepted as atomic remediation commits | Targeted regressions, full pytest, Black, and scoped Flake8 checks |
| AI-009 | `2026-09-18` | Frontend remediation | Scope Todo query keys, clear session cache on logout/account change/401, and restore optimistic snapshots | Frontend auth, API client, Todo hooks/components, unit-test setup | Changes accepted and committed | `npm test` 2/2, `npm run lint`, and `npm run build` pass |
| AI-010 | `2026-09-18` | Evidence synchronization | Update issue status, test results, residual risks, and AI disclosure without marking unexecuted work complete | `docs/BUG_REPORT.md`, `docs/TEST_PLAN.md`, `docs/AI_USAGE.md` | Documentation updated to current commit evidence | Compared against Git history and recorded command output |
| AI-011 | `2026-09-18` | Backend quality and full verification | Document intentional post-`DATABASE_URL` imports, remove the unused incompatible `uv.lock`, and rerun all backend/frontend gates | `backend/tests/conftest.py`, `backend/uv.lock`, assessment evidence in `docs/` | Scoped E402 fix and lockfile removal accepted; evidence synchronized | Python 3.12.12 backend tests 19/19, Black and unfiltered Flake8 pass; frontend tests 2/2, ESLint and build pass |
| AI-012 | `2026-09-18` | Playwright setup | Install and configure Playwright with Chromium, Vite web-server lifecycle, CI-safe retries/artifacts, scripts, and a backend-independent smoke test | Frontend dependencies, Playwright config, smoke test, ignore rules, and documentation | Setup accepted into the worktree; required Tier 2B journeys remain pending | Chromium smoke 1/1, unit tests 2/2, ESLint and production build pass |
| AI-013 | `2026-09-18` | Playwright Journey 1 | Implement the full register/login and Todo lifecycle browser journey with disposable credentials, API-status assertions, stable accessible locators, and post-delete verification | `frontend/e2e/todo-lifecycle.spec.ts`, Todo item accessibility, Playwright port, and assessment evidence | Journey 1 accepted into the worktree; cross-user Journey 2 remains pending | Full Playwright suite 2/2; unit tests 2/2; ESLint/build pass against current Docker backend/PostgreSQL/Redis |
| AI-014 | `2026-09-18` | Playwright Journey 2 | Implement two-session cross-user isolation with disposable accounts, UI/list assertions, B's GET/PUT/DELETE denial, owner-integrity verification, and Todo cleanup | `frontend/e2e/cross-user-isolation.spec.ts` and assessment evidence | Journey 2 accepted into the worktree; Tier 2B now complete | Full Playwright suite 3/3 using three workers; unit tests 2/2; ESLint/build pass against current Docker backend/PostgreSQL/Redis |
| AI-015 | `2026-09-18` | Deterministic E2E data | Replace timestamp data with fixed retry-indexed fixtures, add an allowlisted transactional reset, chain reset into headless/headed/UI scripts, and document exact commands | Backend E2E reset utility, frontend fixture data, package scripts, GUIDE, README, and assessment evidence | Deterministic setup accepted into the worktree | Two consecutive headless runs pass 3/3; second reset deletes prior fixtures; headed `--list` resets and lists 3 tests; Black/Flake8 pass for reset utility |
| AI-016 | `2026-09-18` | Infrastructure hardening | Add health-gated startup, scoped Docker contexts, non-root/multi-stage images, required external configuration, authenticated Redis, and internal-only data-service ports | Compose, Dockerfiles, backend settings/tests, environment templates, GUIDE, and assessment evidence | Tier 3B implementation accepted into the worktree | Compose config/build/cold start pass; all services healthy; app UIDs 999/1000; Redis rejects no-auth; backend 22/22, frontend tests/lint/build pass |
| AI-017 | `2026-09-18` | PostgreSQL performance | Seed an isolated 10k-user/1M-Todo PostgreSQL database; retain exact SQL, plans and all timings; add deterministic Todo order and concurrent composite index migration; measure before/after and migration/write/storage tradeoffs | Todo service/model/test, Alembic migration, performance report and raw benchmark artefacts | Tier 3C implementation accepted into the worktree | Q1 median 22.245→0.056 ms; Q2 20.471→0.064 ms; upgrade/downgrade/re-upgrade pass; backend 23/23, Black and Flake8 pass |
| AI-018 | `2026-09-18`–`2026-09-19` | Final remediation | Implement and verify refresh-token rotation/logout revocation, login-enumeration protection, commit-ordered cache invalidation, email uniqueness, eager Todo loading, bounded pagination, integration coverage, settings/dependency maintenance, and frontend quality fixes | Backend auth/Todo/cache/config/tests; frontend dependencies, routes, dialogs, error handling, Vite configuration; assessment documents | Changes accepted as separate Conventional Commits | Fast backend 34/34; PostgreSQL/Redis integration 2/2; frontend unit 9/9, lint/build, Playwright 4/4; audits report no vulnerabilities |
| AI-019 | `2026-09-19` | Documentation synchronization | Reconcile all project documentation with current source, commits, public API, test scripts, and recorded verification | `GUIDE.md`, frontend README, remediation plan, and assessment documents | Current-state references, commands, and evidence synchronized | Git history and source inspected; documentation diff checked |
| AI-020 | `2026-09-19` | Deployed frontend page-size verification | Diagnose a Todo-list failure from a stale Docker frontend bundle, rebuild the targeted image, and add a browser-level request-contract assertion | Frontend Docker runtime, Journey 1 E2E test, bug report, and test plan | Remediation accepted in `85346dc` | Frontend unit 9/9, ESLint, production build, and Docker-served Journey 1 1/1 pass with `size=100` and HTTP 200 |
| AI-021 | `2026-09-19` | Password-validation contract | Align backend registration/login schemas with the frontend's minimum password rule, keep bcrypt's byte limit, and add API/unit regressions | Backend user schemas/auth route/tests; frontend Zod schema/tests; assessment documents | Accepted in `3d7029d` | Backend 38/38, Black, Flake8; frontend 10/10, ESLint, and production build pass |
| AI-022 | `2026-09-19` | CORS and SQL logging hardening | Restrict credentialed CORS to configured origins, disable SQL echo by default, and add configuration/API regressions | Backend settings, application middleware, Compose/environment template, tests, and assessment documents | Accepted in `2d8bcff` | Backend 40/40, Black, and Flake8 pass |
| AI-023 | `2026-09-19` | Redis-outage resilience | Keep committed Todo mutations successful when Redis invalidation fails, log the event for alerting, and inject a Redis failure in an API regression | Todo mutation helper, backend tests, and assessment documents | Accepted in `08a2643` | Backend 41/41, Black, and Flake8 pass |
| AI-024 | `2026-09-19` | Tag database foundation | Add user-owned Tag and Todo-to-Tag models, a case-insensitive unique name index, mapping/filter indexes, Alembic migration, and database regressions | Backend models, migration, tests, and assessment documents | Accepted in `8e5fe8e` | Backend 44/44, Black, Flake8, and PostgreSQL 16 upgrade → downgrade → re-upgrade pass |
| AI-025 | `2026-09-19` | Tier 4 backend API | Add owner-scoped Tag CRUD, Todo-to-Tag mapping, Todo filters, atomic bulk status updates, cache-key dimensions, and Redis invalidation regressions | Backend routes, schemas, services, fast/integration tests, and assessment documents | Accepted in `7df88c4` | Backend 48/48, Black, Flake8, and PostgreSQL/Redis integration 3/3 pass |
| AI-026 | `2026-09-19` | Tier 4 frontend | Add filter controls, Tag display/management, bulk status controls, full-filter React Query keys, mutation invalidation, validation regressions, and a browser journey | Todo/Tag feature components, API hooks, schemas, unit/E2E tests, GUIDE, and assessment evidence | Accepted in `b5be6e4` | Frontend unit 11/11, ESLint, production build, and Playwright 5/5 pass |
| AI-027 | `2026-09-19` | Per-Todo Tag controls | Add an accessible dialog to attach and detach an owned Tag from an individual Todo, then update the Tier 4 browser journey and documentation | Todo API hooks/components, E2E test, GUIDE, test plan | Accepted in `066ba72` | Frontend unit 14/14, ESLint, production build, and Tier 4 Playwright journey pass |
| AI-028 | `2026-09-19` | Dashboard pagination | Replace the hard-coded first Todo page with stateful page navigation, reset to page 1 on filters, and test the 101st Todo in the browser | Todo dashboard, query regression, E2E fixtures/reset, docs | Accepted in `e53e671` | Frontend unit 15/15, ESLint, production build, and Playwright 6/6 pass |
| AI-029 | `2026-09-19` | JWT endpoint matrix | Add tampered-signature coverage and verify expired/refresh JWT rejection on both protected endpoints; finalize manual-plan evidence | Backend auth tests, `docs/TEST_PLAN.md` | Accepted in `b89416b` | Backend pytest 49/49, Black, and Flake8 pass |
| AI-030 | `2026-09-19` | Documentation synchronization | Reconcile guides, findings, performance limitations, remediation status, test evidence, and this disclosure with the delivered Tier 4, pagination, and JWT work | Project Markdown documentation | Accepted in the current worktree | Source, Git history, and documentation diff reviewed; Markdown whitespace check passes |

If full prompt logs are required, store sanitized logs under `docs/ai-prompts/` and link them here. Never include secrets, access tokens, personal data, private URLs, or hidden evaluation material.

## 4. Material decisions influenced by AI

| Decision | AI contribution | Candidate decision and rationale | Evidence |
|---|---|---|---|
| Prioritize authorization, cache isolation, and JWT before feature work | Identified these as the highest-risk confidentiality/integrity failures | Adopted; regression coverage and fixes were implemented before optional features | Commits `cea96fd` through `b35b042`; fast backend suite now passes 34/34 |
| Target the maximum 115/100 score | Mapped 100 mandatory points plus 15 Tier 4 bonus points | Adopted for planning; mandatory gates must pass before bonus work | README traceability matrix |
| Keep Todo Sharing as specification-only work | Flagged README's explicit instruction not to implement Task 3A | Adopted to prevent scope expansion | `docs/TODO_SHARING_SPEC.md` |
| Track assessment documents while keeping the answer key ignored | Identified the conflict between required `docs/` deliverables and the root ignore rule | Adopted; removed broad `docs/` ignore and retained `docs/ANSWER_KEY.md` | `git check-ignore` verification |
| Keep backend dependencies managed by `requirements.txt` | Identified that the three-line `uv.lock` was generated incidentally, targeted Python 3.13, and was not used by Docker or setup instructions | Adopted; removed the lockfile in standalone commit `23b039e` and used `uv --no-project` only as an isolated test runner | Docker targets Python 3.12; Black targets `py312`; full backend rerun passes on Python 3.12.12 |
| Keep data services internal by default | Recommended removing PostgreSQL/Redis host publications instead of merely binding them to localhost, while preserving administration through `docker compose exec` | Adopted; host-run backend development must use separate local services or an explicit override | `docker compose ps` shows only container ports; GUIDE documents the operational tradeoff |

## 5. Generated or substantially assisted artefacts

| Artefact | Assistance type | Human changes | Validation |
|---|---|---|---|
| `AGENTS.md` | Repository analysis and drafting | Candidate review pending | Compared with README and current code structure |
| `REMEDIATION_PLAN.md` | Planning and risk prioritization | Candidate review pending | Mapped against mandatory and bonus README requirements |
| `docs/BUG_REPORT.md` | Issue inventory, status tracking, and evidence synchronization | Candidate review and final PR link pending | All recorded remediation findings map to commits/tests; Tier 4 is implemented end to end |
| `docs/TEST_PLAN.md` | Test-plan structure, environment metadata, and execution log | Execution evidence acknowledged; independent reviewer was not assigned | Backend/frontend automated reruns and the JWT endpoint matrix are recorded |
| `docs/TODO_SHARING_SPEC.md` | Production-ready specification | Candidate review pending | Complete proposed design compared with README and provided template |
| `docs/PERFORMANCE_REPORT.md` and `docs/performance/` | PostgreSQL benchmark design, raw SQL/plans/timings, safety analysis | Candidate review pending | PostgreSQL 16.15 evidence on 10k users/1M Todos; before/after results, storage/write impact, and limitations retained |
| `docs/AI_USAGE.md` | Disclosure structure and ongoing assistance log | Candidate confirmation and final sign-off pending | Cross-checked against material assistance, Git history, and recorded verification |
| Backend auth/Todo/cache/config source and tests | Regression design and implementation assistance | Candidate review remains required | Current non-root container suite 49/49; Black and unfiltered Flake8 pass; PostgreSQL/Redis integration 3/3 passes |
| Frontend auth/query/session/Tag source and tests | Query-key/session/Tag design and implementation assistance | Candidate review remains required | Unit tests 15/15, ESLint, production build, and Playwright 6/6 pass |
| Frontend Playwright setup and smoke test | Dependency/configuration and test scaffolding assistance | Both required journeys complete; candidate review pending | Playwright 1.63.0 suite 6/6; headless/headed/UI commands documented |
| Frontend Playwright lifecycle Journey 1 | Browser-flow implementation, disposable data, and evidence synchronization | Candidate review pending | Registration/login and create/edit/complete/delete/logout pass; final deleted-resource GET returns 404 |
| Frontend Playwright cross-user Journey 2 | Two-context authorization/isolation flow and evidence synchronization | Candidate review pending | B list/UI excludes A data; B GET/PUT/DELETE return 404; A Todo remains unchanged; suite 6/6 passes |
| Deterministic Playwright data setup | Allowlisted reset design, retry-indexed fixtures, scripts, and documentation | Candidate review pending | Exact 15-email reset across five fixture roles; headless/headed/UI commands are documented |
| Docker/Compose infrastructure hardening | Readiness, build-context, privilege, secret/configuration, Redis-auth, and port-isolation implementation | Candidate review pending | Cold start/build pass; four services healthy; non-root IDs and Redis auth verified; backend/frontend regressions pass |
| PostgreSQL Todo index and benchmark | Index selection, deterministic ordering, migration safety, raw evidence, and performance report | Candidate review pending | Isolated 1M-row PostgreSQL benchmark; concurrent migration rollback/reapply and current backend 34/34 regression evidence |

Add source code and test files to this table when AI materially contributes to them.

## 6. Rejected suggestions and corrections

| Suggestion | Why rejected or changed | Final approach |
|---|---|---|
| Treat unfamiliar Python package names as evidence of malware | Package names alone were insufficient, and official package metadata showed the dependency chain | Do not classify them as malicious; still reduce unused production dependencies later |
| Install missing dependencies immediately during the read-only audit | Installation was not required to identify the initial environment blocker and would mutate the workspace | Record the blocker first; install through the approved project setup in the baseline phase |
| Implement Todo Sharing while addressing the assessment | README explicitly states Task 3A is specification-only | Produce the specification without implementation unless separately requested |

## 7. Verification performed by the candidate

- [ ] Reviewed every changed line and related call path.
- [ ] Confirmed behavior against `README.md` and API contracts.
- [x] Ran relevant backend tests.
- [x] Ran relevant frontend lint/build/tests.
- [x] Ran PostgreSQL/Redis integration checks where mocks are insufficient.
- [x] Reviewed migrations and rollback behavior.
- [x] Validated Docker/runtime configuration.
- [x] Removed tracked environment files and verified no real secrets, personal data, or private context were added.
- [ ] Recorded checks that could not be run and why.

## 8. Limitations

- AI output can be incomplete or incorrect and is not treated as test evidence.
- Suggested security controls require threat-model and integration review.
- Suggested database indexes require measured PostgreSQL evidence; the current benchmark supplies PostgreSQL evidence but remains local, warm-cache, and workload-specific.
- Fixed auth, ownership, partial-update, cache, and frontend-session findings have automated regression evidence. A forced component-level optimistic-mutation failure and selected exploratory manual cases remain useful additional coverage.
- The first backend test attempt was blocked because the system Python environment lacked `pytest`; later isolated and non-root container runs pass, with the current fast suite at 49/49.
- Backend fast tests use SQLite and a stateful Redis mock; separate PostgreSQL/Redis integration and refresh-concurrency evidence pass 3/3. The fast suite injects post-commit invalidation failure and Tier 4 boundaries, while temporary PostgreSQL 16/Redis 7 containers validate the Tag migration plus real cache versioning.
- Both required Playwright journeys pass; same-context account-switch cache behavior still has unit coverage only.
- Candidate review, identity spelling confirmation, and final attestation are pending.

## 9. Final attestation

To be completed by the candidate before submission after reviewing the implementation, tests, specifications, tradeoffs, and this assistance log.

**Candidate:** Nguyen Dinh Duc — pending sign-off

**Date:** Pending
