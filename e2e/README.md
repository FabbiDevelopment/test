# Playwright E2E

Start the application first with `docker compose up --build`.

```powershell
cd e2e
npm install
npx playwright install chromium
npx playwright test
npx playwright test --headed
```

Use `BASE_URL=http://localhost:3000` to target another frontend URL. Tests create unique users and use separate browser contexts for isolation.
