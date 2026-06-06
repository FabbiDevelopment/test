# Repository Guidelines

## Project Structure & Module Organization

This is a full-stack Todo application. Backend code lives in `backend/app/`: `api/v1/` contains FastAPI routes, `core/` settings/security/Redis, `db/` database setup, `models/` SQLAlchemy models, `schemas/` Pydantic contracts, and `services/` business logic. Migrations are in `backend/alembic/`; backend tests are in `backend/tests/`.

Frontend code lives in `frontend/src/`. Use `components/ui/` for shared shadcn/ui primitives, `features/` for auth/todo modules, `lib/` for API/query utilities, `pages/` for route screens, and `router/` for React Router setup. Static assets belong in `frontend/public/`.

## Build, Test, and Development Commands

- `docker-compose up --build`: build and run frontend, backend, PostgreSQL, and Redis.
- `docker compose exec backend python -m app.db.seed`: seed demo users and todos after services are running.
- `cd backend && alembic upgrade head`: apply database migrations.
- `cd backend && uvicorn app.main:app --reload --port 8000`: run the API locally without Docker.
- `cd backend && pytest tests/ -v`: run backend tests.
- `cd frontend && npm install`: install frontend dependencies.
- `cd frontend && npm run dev`: start the Vite dev server.
- `cd frontend && npm run build`: type-check and build the frontend.
- `cd frontend && npm run lint`: run ESLint.

## Coding Style & Naming Conventions

Backend Python targets 3.12. Format with Black from `backend/pyproject.toml` using 88-character lines; Flake8 allows 120 characters and ignores `E203`/`W503`. Prefer existing async SQLAlchemy service patterns and keep Pydantic schemas explicit at API boundaries.

Frontend is TypeScript, React 19, Vite, and Tailwind CSS. Use PascalCase for components, camelCase for functions/variables, and colocate feature hooks/components under `frontend/src/features/<feature>/`. Keep React Query keys user- and filter-scoped.

## Testing Guidelines

Backend tests use Pytest with async support from `backend/pytest.ini`. Add tests in `backend/tests/` for auth, authorization, cache invalidation, migrations, and service behavior when changing backend logic. Name files `test_<area>.py` and functions `test_<expected_behavior>`.

Frontend test tooling is not currently defined; run `npm run lint` and `npm run build` after frontend changes. Add focused frontend tests only after introducing a test runner.

## Commit & Pull Request Guidelines

Recent history uses short conventional-style subjects such as `feat: initial commit`. Continue with `type: concise summary`, for example `fix: isolate todo cache by user`.

For PRs, include a clear description, linked issue or assessment item, commands run, known limitations, and screenshots for UI changes. The assessment workflow expects bug findings, reasoning, fix proposals, and verification notes in the PR description. Do not commit private credentials; document configuration in `.env.example`.
