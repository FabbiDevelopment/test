# E2E Tests (Playwright)

## Prerequisites

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`
- Start stack: `docker compose up -d` from repo root

## Install

```bash
npm install
npx playwright install chromium
```

## Run

```bash
# Headless
npx playwright test

# Headed
npx playwright test --headed

# UI mode
npx playwright test --ui
```

## Scenarios

1. **user-journey.spec.ts** — Register → create todo → toggle completed → logout  
2. **cross-user-isolation.spec.ts** — User A private todo not visible to User B
