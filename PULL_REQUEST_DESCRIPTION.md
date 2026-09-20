# Full-Stack Engineering & QA Assessment Submission

**Candidate**: Nguyen Quang Huy  
**Branch**: `assessment/nguyen-quang-huy`  
**Target**: `main`  

---

## 📌 Executive Summary
This Pull Request delivers comprehensive solutions across all assessment tiers:
- **Tier 1**: Fixed 5 critical security, authorization, caching, and state management bugs.
- **Tier 2**: Implemented automated test suites with 100% pass rate (29 pytest cases, 3 Playwright E2E journeys) and authored a formal QA manual test plan.
- **Tier 3**: Produced an enterprise-grade technical specification for Todo Sharing, optimized Docker infrastructure with healthchecks and multi-stage production builds, and benchmarked PostgreSQL index performance.
- **Tier 4 (Bonus Extension)**: Fully engineered Todo Tags, multi-criteria filtering, bulk status updates, bulk deletions, and GIN Trigram substring search acceleration.

---

## 🐞 Tier 1: Bug Hunting & Critical Fixes Report

### Bug 1: JWT Expiration Verification Disabled (Bypass)
- **Location**: `backend/app/core/security.py` -> `verify_token()`, line 56
- **Severity**: **Critical**
- **Reason**: Token decoding passed `options={"verify_exp": False}`, allowing expired or leaked access tokens to access protected endpoints indefinitely.
- **Fix**: Removed `options={"verify_exp": False}` to let python-jose strictly validate `exp` timestamps.

### Bug 2: Broken Object-Level Authorization (IDOR / BOLA)
- **Location**: `backend/app/api/v1/todos.py` -> `get_todo()`, `update_existing_todo()`, `delete_existing_todo()`
- **Severity**: **Critical**
- **Reason**: Operations fetched records solely by `todo_id` without verifying `todo.user_id == current_user.id`. Any authenticated user could view, update, or delete other users' private todos.
- **Fix**: Added `get_todo_by_id_and_user()` and ownership assertions before reading or mutating resources.

### Bug 3: Boolean Toggle Failure on Todo Completion Status
- **Location**: `backend/app/api/v1/todos.py` -> `update_existing_todo()`
- **Severity**: **High**
- **Reason**: The code used `if todo_data.completed:`, which evaluated to `False` in Python when passing `{"completed": false}`. Completed todos could never be toggled back to active.
- **Fix**: Changed logic to use `todo_data.model_dump(exclude_unset=True)` and checked `completed is not None`.

### Bug 4: Partial Update Overwriting Description with None
- **Location**: `backend/app/api/v1/todos.py` -> `update_existing_todo()`
- **Severity**: **High**
- **Reason**: Calling `todo_data.model_dump()` without `exclude_unset=True` included unset fields as `None`, overwriting existing descriptions when only `title` was updated.
- **Fix**: Applied `exclude_unset=True` to preserve unmodified attributes.

### Bug 5: Shared Global Redis Cache Key & Cache Leak
- **Location**: `backend/app/api/v1/todos.py` -> `list_todos()`
- **Severity**: **Critical**
- **Reason**: Used a single hardcoded cache key `"todos:list"`. The first user who loaded todos cached their data for all users, causing cross-user data leakage. Mutating actions also failed to invalidate cache.
- **Fix**: User-scoped cache keys (`todos:user:{id}:...`) and added `delete_user_todos_cache()` invalidation on create, update, delete, tag attach/detach, and bulk actions.

*(Full report available at [`docs/BUG_REPORT.md`](docs/BUG_REPORT.md))*

---

## 🧪 Tier 2: Testing Strategy & Implementation

### Reproduction Commands
```bash
# 1. Run Backend Automated Pytest Suite (via Docker)
docker compose run --rm backend pytest tests/ -v

# 2. Run Playwright E2E Suite (Headless)
npx playwright test

# 3. Run Playwright E2E Suite (Headed / UI Mode)
npx playwright test --headed
```

### Verification Results
- **Pytest**: `29 passed, 1 warning in 21.78s` (covers authentication, JWT tampering, cross-user isolation, boolean toggle, partial update, tag cascades, and bulk delete).
- **Playwright E2E**: `3 passed in 16.2s` (`data-isolation.spec.ts`, `user-journey.spec.ts`, and `tags-and-bulk-actions.spec.ts`).
- **Frontend Code Quality**: `npm run lint` (0 errors, 0 warnings), `npm run build` (success).

*(Structured test matrix available at [`docs/TEST_PLAN.md`](docs/TEST_PLAN.md))*

---

## ⚡ Tier 3: Advanced Engineering Skills

### 3A. Technical Specification: Todo Sharing
- Complete production-ready design document covering user stories, RBAC permissions (`owner`, `editor`, `viewer`), DB schema with composite unique constraints, audit events, and Redis cache invalidation.
- *Document*: [`docs/TODO_SHARING_SPEC.md`](docs/TODO_SHARING_SPEC.md)

### 3B. Docker & Infrastructure Optimization
- Implemented dependent healthchecks (`pg_isready`, `redis-cli ping`) with `condition: service_healthy` to eliminate startup race conditions.
- Added comprehensive `.dockerignore` files to prevent image bloat and secret leakage.
- Created multi-stage production setup with Alpine base images in `docker-compose.prod.yml`.
- *Document*: [`docs/DOCKER_OPTIMIZATION.md`](docs/DOCKER_OPTIMIZATION.md)

### 3C. Database Indexing & Query Tuning
Benchmarked on a dataset of **1,000,000 todos** across **10,000 users**:

| Query Scenario | Execution Time (Before) | Execution Time (After Index) | Speedup |
| :--- | :--- | :--- | :--- |
| User Todos Filtered by `completed` | 184.2 ms (Seq Scan) | 1.12 ms (Index Scan) | **~164x faster** |
| User Todos Ordered by `created_at` | 212.5 ms (Sort + Seq Scan) | 1.45 ms (Index Scan) | **~146x faster** |
| Multi-criteria Keyword Search | 340.8 ms (Seq Scan + ILIKE) | 4.80 ms (GIN Trigram Scan) | **~71x faster** |

- Applied migrations: `901edbc49e0f_add_composite_index_on_todos.py` and `b1e8f9a2c3d4_add_fulltext_search_index_on_todos.py`.
- *Document*: [`docs/DATABASE_BENCHMARK.md`](docs/DATABASE_BENCHMARK.md)

---

## 🏷️ Tier 4: Todo Tags, Filtering & Bulk Actions
- **Tags Management**: Full CRUD (`GET`, `POST`, `PATCH`, `DELETE /tags`) with case-insensitive uniqueness per user.
- **Many-to-Many Association**: Table `todo_tags` with ON DELETE CASCADE constraints.
- **Bulk Actions**:
  - `PATCH /api/v1/todos/bulk-status`: Batch chunked status updates (500/batch) with transaction rollback.
  - `POST /api/v1/todos/bulk-delete`: Batch chunked deletions with tag association cleanup and user cache purge.
- **Frontend UI**: Integrated TagManager modal, multi-filter toolbar, selection checkboxes, and animated `BulkActionBar`.

---

## 🤖 AI Assistance Disclosure
- **Tools Used**: Google Antigravity IDE (Gemini Model / Claude Sonnet).
- **Configuration & Context**: Project architecture guidelines, Conventional Commits (`.commitlintrc.json`), Pydantic/OpenAPI schema contracts.
- **Assisted Areas**:
  - Drafting comprehensive technical specifications (`docs/TODO_SHARING_SPEC.md`).
  - Formulating PostgreSQL GIN trigram indexing and `EXPLAIN ANALYZE` benchmarks.
  - Generating boilerplates for Playwright E2E tests and UI component styling.
  - Reviewing code against OWASP practices (IDOR, SQL injection, cache poisoning).
- **Human Verification**: All code logic, database migrations, unit tests (29 passing tests), and Playwright runs were validated locally and manually reviewed.
