import type { Page } from "@playwright/test";

export function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@example.com`;
}

export const TEST_PASSWORD = "password123";

/** Registers a brand-new user through the UI and lands on the dashboard. */
export async function registerViaUI(page: Page, email: string, password = TEST_PASSWORD) {
  await page.goto("/register");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.locator("#confirmPassword").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await page.waitForURL("/");
}

/** Logs an already-registered user in through the UI and lands on the dashboard. */
export async function loginViaUI(page: Page, email: string, password = TEST_PASSWORD) {
  await page.goto("/login");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();
  await page.waitForURL("/");
}

/** Creates a todo through the "Add Todo" dialog. Assumes the dashboard is already open. */
export async function createTodoViaUI(page: Page, title: string, description?: string) {
  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.locator("#title").fill(title);
  if (description) {
    await page.locator("#description").fill(description);
  }
  await page.getByRole("button", { name: "Create" }).click();
  // Dialog closes once the mutation succeeds and the list refetches.
  await page.getByText(title).waitFor({ state: "visible" });
}
