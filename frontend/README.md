# Fabbi Todo frontend

React/Vite frontend for the Todo assessment.

## Local development

```bash
npm ci
npm run dev
```

The development server uses `VITE_API_URL` from `.env` and expects the backend
at `http://localhost:8000` by default.

## Unit tests and quality checks

```bash
npm test
npm run lint
npm run build
```

## Playwright

Start the current backend stack from the repository root:

```bash
docker compose up -d --build --wait postgres redis backend
```

Then install the pinned Node dependencies and Chromium browser binary:

```bash
npm ci
npm run test:e2e:install
```

Run the Playwright suite headless or headed. Both commands reset the allowlisted
E2E users before launching Playwright:

```bash
npm run test:e2e          # headless
npm run test:e2e:headed   # headed browser
npm run test:e2e:ui
```

The reset can also be run explicitly with `npm run test:e2e:prepare`. It deletes
Todos first and then users for only these deterministic fixture identities:

| Role | Email pattern | Password | Todo title |
|---|---|---|---|
| Journey 1 | `e2e-journey1-r{0..2}@example.com` | `E2eTodo@123` | `E2E Journey 1 Todo r{retry}` |
| Journey 2 user A | `e2e-journey2-a-r{0..2}@example.com` | `E2eTodo@123` | `E2E Journey 2 Todo r{retry}` |
| Journey 2 user B | `e2e-journey2-b-r{0..2}@example.com` | `E2eTodo@123` | None |
| Tier 4 | `e2e-tier4-r{0..2}@example.com` | `E2eTodo@123` | `Tier 4 tagged work r{retry}` |
| Pagination | `e2e-pagination-r{0..2}@example.com` | `E2eTodo@123` | `Pagination Todo {1..101}` |

Retry indexes 0–2 match the configured initial attempt plus two CI retries. The
backend reset refuses to run unless `E2E_ALLOW_RESET=1`; the npm prepare script
sets this confirmation flag. Do not run multiple suites concurrently against
the same backend because each suite resets the same fixed fixture namespace. UI
mode resets once at startup; restart `npm run test:e2e:ui` before rerunning a
registration journey after it has created its fixture account.

Playwright starts a dedicated Vite server on `http://127.0.0.1:4173` when no server is
already running. Set `PLAYWRIGHT_BASE_URL` to test an existing frontend; when
this variable is set, Playwright does not start its own Vite process:

```bash
PLAYWRIGHT_BASE_URL=http://localhost:3000 npm run test:e2e
```

The smoke test validates the browser setup without backend data. A structured
error regression intercepts registration and confirms that a FastAPI 422
`detail` array is rendered safely. Journey 1 uses the deterministic Journey 1
account to cover registration, logout/login, Todo creation, editing, completion
by clicking its name, deletion, and final logout against the backend at `http://localhost:8000`.
Journey 2 uses two isolated browser contexts and verifies that user B cannot
see, read, update, or delete user A's Todo. The pagination regression creates
101 Todos, verifies the 101st item is available on page 2, and verifies applying
a filter returns the dashboard to page 1. The Tier 4 journey creates a Tag,
attaches it to a Todo, filters by it, and bulk-updates selected Todos. The
current suite therefore has six Chromium tests.

Failure artifacts are written to `test-results/`. The HTML report is written to
`playwright-report/` and can be opened with:

```bash
npm run test:e2e:report
```
