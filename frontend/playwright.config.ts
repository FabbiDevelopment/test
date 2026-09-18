import { defineConfig, devices } from "@playwright/test";

/**
 * The full stack (postgres + redis + backend + frontend) must already be
 * running before `npx playwright test`:
 *
 *   docker compose up -d          # postgres, redis, backend, frontend
 *   # or, for local dev servers instead of the frontend container:
 *   docker compose up -d postgres redis backend
 *   cd frontend && npm run dev    # serves on http://localhost:5173
 *
 * Point E2E_BASE_URL at whichever one you started (defaults to the Vite
 * dev server).
 */
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // tests create real users/todos against a shared DB
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:5173",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
