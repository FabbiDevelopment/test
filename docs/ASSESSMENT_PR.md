# Pull Request — Developer Assessment Submission

**Branch:** `assessment/nguyen-tuyen-canh` → `main`  
**AI disclosure:** Phát triển có hỗ trợ **Cursor AI** (phân tích bug, test, Docker, docs, Level 4 tags). Đã review và chạy pytest local.

---

## Tier 1 — Bug findings & fixes

| Location | Severity | Reason | Fix |
|----------|----------|--------|-----|
| `backend/app/core/security.py` — `verify_token()` | Critical | `verify_exp: False` — JWT hết hạn vẫn hợp lệ | THÊM `verify_exp: True` + comment SAI |
| `backend/app/api/deps.py` — `get_current_user()` | Critical | Refresh token dùng như access token | THÊM check `type == "access"` |
| `backend/app/api/v1/todos.py` — cache | Critical | Key global → rò rỉ todo cross-user | THÊM key `user + page + size + filter hash` |
| `backend/app/api/v1/todos.py` — GET/PUT/DELETE | Critical | IDOR — không check owner | THÊM `403` khi `user_id != owner` |
| `backend/app/api/v1/auth.py` — login | High | 404 vs 401 → user enumeration | THÊM 401 message chung |
| `backend/app/api/v1/todos.py` — update | High | `completed` bỏ qua False; partial wipe description | THÊM `exclude_unset=True` |
| `backend/app/core/redis.py` | High | Không invalidate theo prefix | THÊM `delete_by_prefix()` |
| `frontend/.../todos.ts` | High | `queryKey` thiếu filters | THÊM full filter trong key |
| `frontend/.../useAuth.ts`, `auth.ts` | High | Logout không clear React Query | THÊM `queryClient.clear()` |
| `frontend/.../todos.ts` onError | Medium | Optimistic update không rollback | THÊM restore `previousQueries` |

**Known open:** `POST /auth/logout` chưa blacklist JWT (server-side token vẫn valid tới exp).

---

## Tier 2 — Testing

### 2A Backend

```bash
cd backend
pytest tests/ -v
```

**Result:** 29 passed (security, authorization, business logic, cache, tags, regression auth/todos).

### 2B E2E (Playwright)

**Prerequisites:** `docker compose up -d` (frontend :3000, backend :8000)

```bash
cd e2e
npm install
npx playwright install chromium
npx playwright test          # headless
npx playwright test --headed
npx playwright test --ui
```

Scenarios: full user journey; cross-user isolation (2 browser contexts).

### 2C Manual test plan

`docs/TEST_PLAN.md`

---

## Tier 3

| Task | Deliverable |
|------|-------------|
| 3A Todo sharing spec | `docs/TODO_SHARING_SPEC.md` |
| 3B Docker | `.dockerignore`, multi-stage Dockerfiles, `docker-compose.yml` healthchecks, `docker-compose.prod.yml` |
| 3C Indexing | `alembic/versions/002_add_todo_performance_indexes.py`, `docs/PERFORMANCE_INDEXING.md` |

**Seed large dataset:**

```bash
docker compose exec -e SEED_USERS=10000 -e SEED_TODOS=1000000 backend python -m app.db.seed
```

---

## Tier 4 — Tags, filters, bulk

- Backend: `tags`, `todo_tags`, filter query params, bulk-status, cache invalidation on tag ops
- Frontend: `TagManager`, `TodoFilterBar`, bulk select, tag badges

---

## Reproduce locally

```bash
docker compose up -d --build
cd backend && pytest tests/ -v
cd ../e2e && npx playwright test
```
