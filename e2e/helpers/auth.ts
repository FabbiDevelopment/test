import { expect, type Page } from "@playwright/test";

export const TEST_PASSWORD = "Password123!";

export function uniqueEmail(prefix: string): string {
  const uniquePart = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return `${prefix}-${uniquePart}@example.com`;
}

export async function registerUser(
  page: Page,
  email: string,
  password = TEST_PASSWORD,
): Promise<void> {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText(email, { exact: true })).toBeVisible();
}

export async function loginUser(
  page: Page,
  email: string,
  password = TEST_PASSWORD,
): Promise<void> {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();

  await expect(page).toHaveURL("/");
  await expect(page.getByText(email, { exact: true })).toBeVisible();
}
