# AGENTS.md

## Purpose and source of truth

This repository is a full-stack engineering assessment built around an intentionally flawed Todo application. Read `README.md` before starting any substantial task. It defines the assessment tiers, minimum deliverables, and evaluation criteria. Use `GUIDE.md` for setup commands and the files under `templates/` for required document structure.

The README describes the whole assessment, not an instruction to implement every tier on every request. Follow the user's requested scope. In particular:

- Todo Sharing in Tier 3A is a specification-writing task, not an implementation task.
- Todo Tags, Filtering, and Bulk Actions are optional Tier 4 work unless explicitly requested.
- Do not make unrelated cosmetic changes while fixing correctness, security, or infrastructure issues.

When documentation and code disagree, treat the code as the current runtime behavior, then either update the documentation as part of the same scoped change or report the discrepancy.

## Repository map

- `backend/app/main.py`: FastAPI application, lifespan, CORS, and router registration.
- `backend/app/api/`: HTTP dependencies and v1 route handlers.
- `backend/app/services/`: database-facing authentication and Todo operations.
- `backend/app/models/`: SQLAlchemy 2.0 ORM models.
- `backend/app/schemas/`: Pydantic v2 request and response models.
- `backend/app/core/`: settings, JWT/password helpers, and the Redis client.
- `backend/app/db/`: async SQLAlchemy session management and bulk seed script.
- `backend/alembic/`: PostgreSQL migrations. Schema changes require a new migration.
- `backend/tests/`: async pytest API tests using SQLite and a mocked Redis dependency.
- `frontend/src/features/`: feature-oriented auth and Todo API/hooks/components/schemas.
- `frontend/src/components/ui/`: shared shadcn/Radix-style UI primitives.
- `frontend/src/lib/`: Axios client, React Query client, and shared utilities.
- `frontend/src/router/` and `frontend/src/pages/`: routing and page composition.
- `docker-compose.yml`: local PostgreSQL, Redis, backend, and frontend stack.
- `templates/`: templates for the technical specification and manual test plan.

## Technology and runtime conventions

### Backend

- Target Python 3.12 and use async FastAPI, SQLAlchemy, asyncpg, and Redis APIs end to end.
- Keep route handlers focused on HTTP concerns. Put reusable persistence/business logic in `app/services/`.
- Obtain database sessions through `get_db`; it commits after a successful request and rolls back on exceptions.
- Use Pydantic schemas at API boundaries. For partial updates, preserve omitted fields and distinguish an omitted value from explicit `false` or `null` where the contract permits it.
- Store and compare timezone-aware UTC timestamps.
- Never modify an existing applied migration to change the schema. Add a new Alembic revision and ensure models and migrations stay aligned.
- Black is configured for 88 columns in `backend/pyproject.toml`. Flake8 currently permits 120 columns and excludes Alembic; prefer Black-compatible formatting for new Python code.

### Frontend

- Use React 19, TypeScript strict mode, Vite, Tailwind CSS v4, React Router, TanStack React Query, Axios, react-hook-form, and Zod.
- Use the `@/` alias for imports from `frontend/src`.
- Keep remote state in React Query and form validation in Zod schemas. Do not duplicate server state in ad hoc component state.
- Query keys must include every input that can change the response, including user identity, pagination, filters, and sorting.
- Mutations must invalidate or update all affected queries. Optimistic updates must snapshot and restore data on failure.
- Use stable entity IDs as React list keys, not array indexes.
- Match frontend validation to backend validation and preserve useful API errors without exposing sensitive details.

## Security and data-isolation invariants

The application intentionally contains security and correctness defects. Do not assume existing behavior is safe merely because an existing happy-path test passes.

- Every read, update, and delete of user-owned data must be scoped by the authenticated user's ID in the database query. Prefer a not-found response for inaccessible objects when that avoids resource enumeration.
- JWT verification must validate signature, expiration, required claims, and token type. Access-only dependencies must reject refresh tokens.
- Refresh and logout behavior must follow an explicit revocation/rotation strategy. A success response alone is not token invalidation.
- Authentication errors should not reveal whether a particular email exists.
- Redis cache keys for Todo lists must include the user and all query parameters. All successful Todo mutations must invalidate the relevant user-scoped cache entries.
- Backend partial updates must correctly persist `completed=false` and must not erase fields omitted by the client.
- React Query data must not survive an account change in a way that exposes the previous user's data. Clear user-scoped cache on logout and failed authentication transitions.
- Never place real secrets in `.env`, source files, Compose files, images, logs, fixtures, or documentation. The tracked `.env` files currently contain development placeholders; do not replace them with credentials.
- Treat open CORS, database query logging, publicly bound database/cache ports, unauthenticated Redis, and root containers as development-only risks to address when working on infrastructure.

Before changing one of these areas, add or identify a regression test that demonstrates the intended boundary.

## Known baseline hotspots

Re-check these against the current branch before relying on them; remove or update this section when the underlying behavior is fixed.

- JWT decoding in `backend/app/core/security.py` disables expiration verification, while `get_current_user` does not enforce an access-token type.
- Todo detail/update/delete lookups are not owner-scoped.
- The backend Todo list cache uses a global key and mutations do not invalidate it.
- Todo updates only apply `completed` when the submitted value is truthy.
- Todo list queries lack deterministic ordering and currently perform an extra user lookup for every row.
- Frontend Todo query keys omit pagination/user context, logout does not clear React Query data, and optimistic update errors do not restore the snapshot.
- The existing Docker stack has no healthchecks or readiness conditions and contains development credentials.
- Existing tests primarily cover happy paths; they are not proof of authorization, cache, or token correctness.

## Setup and common commands

Prefer Docker Compose v2 syntax (`docker compose`). The current Docker backend runs migrations on container startup.

```bash
cp .env.example .env
docker compose up --build
docker compose exec backend python -m app.db.seed
```

Services are expected at:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

Local backend setup:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
python -m app.db.seed
uvicorn app.main:app --reload --port 8000
```

Local frontend setup:

```bash
cd frontend
npm ci
npm run dev
```

Use `npm ci` for reproducible installs while `package-lock.json` is present. If dependency declarations change, update and commit the lockfile in the same change.

## Validation

Run the checks relevant to the files changed. Do not claim a check passed if its dependencies or required services were unavailable.

Backend:

```bash
cd backend
pytest tests/ -v
black --check .
flake8 app tests
```

Frontend:

```bash
cd frontend
npm run lint
npm run build
```

There is currently no frontend unit-test script and Playwright is not installed. If implementing Tier 2B, add an explicit Playwright configuration, dependencies, deterministic test data/setup, and documented headless/headed commands. Do not describe E2E tests as available until this setup exists.

The pytest suite uses `sqlite+aiosqlite:///./test.db` and overrides Redis with mocks. This is useful for fast API regression tests, but it does not validate PostgreSQL-specific migrations/indexes, Redis key behavior across real requests, container readiness, or production configuration. Use PostgreSQL/Redis integration tests or the Docker stack when those behaviors matter. A cache test may need a shared mock instance rather than the current per-dependency-call mock.

For database performance work, use PostgreSQL with representative data and record the exact SQL, dataset size, `EXPLAIN ANALYZE` output, and before/after timings. SQLite results are not acceptable evidence for Tier 3C.

## README assessment contract

When the user asks to complete the assessment, preserve these minimums from `README.md`:

1. Tier 1: report impactful findings and implement at least five meaningful fixes, including at least two backend fixes and one frontend fix.
2. Tier 2A: add backend tests for at least three listed critical scenarios, favoring expired/tampered JWTs, cross-user authorization, false boolean updates, partial-update preservation, and cache invalidation.
3. Tier 2B: add at least two Playwright journeys: the complete user flow and cross-user isolation.
4. Tier 2C: provide a structured manual test plan with preconditions, steps, expected/actual results, severity, and priority.
5. Tier 3A: write `docs/TODO_SHARING_SPEC.md`; do not implement Todo Sharing unless separately requested.
6. Tier 3B: implement at least three requested Docker/infrastructure improvements and explain their production impact.
7. Tier 3C: add an Alembic index migration and document measured PostgreSQL performance before and after it, including tradeoffs.
8. Tier 4: implement tags/filtering/bulk actions only when explicitly included in scope.

The root `.gitignore` currently ignores the entire `docs/` directory even though the README requires `docs/TODO_SHARING_SPEC.md`. When creating required deliverables under `docs/`, narrow the ignore rules so intended documents are tracked while `docs/ANSWER_KEY.md` remains ignored. Verify with `git status`; do not depend on an ignored deliverable being present only in the working tree.

## Infrastructure changes

- Add service healthchecks and use readiness-aware `depends_on` behavior when addressing cold starts.
- Add scoped `.dockerignore` files for backend and frontend build contexts.
- Keep development convenience separate from production configuration.
- Avoid unpinned global package installs and unnecessary build tools in final images.
- Run application processes as non-root where practical.
- Keep secrets out of image layers and source-controlled Compose defaults; document how operators supply them.
- Do not publish PostgreSQL or Redis ports in production unless required and protected.

## Git and change discipline

- Preserve unrelated user changes and keep patches focused.
- Do not commit generated files such as `node_modules`, `dist`, `test.db`, caches, logs, coverage output, local virtual environments, or private tool metadata.
- Do not commit, push, rewrite history, or open a pull request unless explicitly requested.
- If commits are requested, use the configured Conventional Commit types, for example `fix(auth): enforce access token expiration` or `test(todos): cover cross-user access`.
- Keep schema changes, their migration, tests, and relevant documentation together.
- Before handoff, inspect `git diff` and `git status`, run proportionate checks, and clearly report anything not run.

## Definition of done

A change is complete only when:

- the requested scope is implemented without silently expanding into optional tiers;
- security and ownership rules hold at the persistence boundary, not only in the UI;
- affected cache and client-state paths remain isolated per user;
- regression tests cover the bug or feature's important success and failure paths;
- migrations and lockfiles are included when required;
- documentation and run commands reflect the final behavior;
- relevant lint, build, test, integration, or benchmark evidence is reported accurately.
