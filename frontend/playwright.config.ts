import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  projects: [
    { name: "backend-e2e", testMatch: "todo-journey.spec.ts" },
    { name: "session-cache", testMatch: "session-isolation.spec.ts" },
  ],
  use: {
    baseURL: "http://127.0.0.1:5179",
    channel: process.env.PLAYWRIGHT_CHANNEL,
    trace: "retain-on-failure",
  },
  webServer: {
    command: "npm run dev -- --host 127.0.0.1 --port 5179 --strictPort",
    url: "http://127.0.0.1:5179",
    reuseExistingServer: !process.env.CI,
    env: { VITE_API_URL: process.env.VITE_API_URL || "http://localhost:8000" },
  },
});
