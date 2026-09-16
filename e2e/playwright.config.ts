import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright config — Cấu hình E2E test suite.
 * THÊM: setup từ đầu trong thư mục e2e/ theo yêu cầu assessment Level 2B.
 *
 * Prerequisites / Điều kiện tiên quyết:
 *   docker compose up -d   (backend :8000, frontend :3000)
 */
export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // tránh race condition khi dùng chung DB
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  reporter: [["html", { open: "never" }], ["list"]],
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  timeout: 30_000,
});
