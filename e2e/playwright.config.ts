import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests",
  fullyParallel: false, // run sequentially to avoid cross-user data conflicts
  retries: 1,
  timeout: 30_000,
  reporter: [["list"], ["html", { open: "never" }]],

  use: {
    baseURL: "http://localhost:3000",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    trace: "on-first-retry",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  // Assumes docker-compose up is already running
  webServer: {
    command: "echo 'App already running via docker-compose'",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 10_000,
  },
});
