import { expect, test } from "@playwright/test";
import type { Page } from "@playwright/test";

function uniqueEmail(prefix: string) {
  return `${prefix}-${Date.now()}@example.com`;
}

async function register(page: Page, email: string) {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill("Password@123");
  await page.getByLabel("Confirm Password").fill("Password@123");
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByText("My Todos")).toBeVisible();
}

test("register, create, toggle, and logout", async ({ page }) => {
  await register(page, uniqueEmail("journey"));

  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill("E2E Todo");
  await page.getByLabel("Description (optional)").fill("Created by Playwright");
  await page.getByRole("button", { name: "Create" }).click();

  const todo = page.getByText("E2E Todo");
  await expect(todo).toBeVisible();
  const todoItem = todo.locator("..").locator("..");
  await todoItem.getByRole("checkbox").click();
  await expect(todo).toHaveClass(/line-through/);

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("user data is isolated between browser sessions", async ({ browser }) => {
  const ownerContext = await browser.newContext();
  const ownerPage = await ownerContext.newPage();
  await register(ownerPage, uniqueEmail("owner"));

  await ownerPage.getByRole("button", { name: "Add Todo" }).click();
  await ownerPage.getByLabel("Title").fill("Private E2E Todo");
  await ownerPage.getByRole("button", { name: "Create" }).click();
  await expect(ownerPage.getByText("Private E2E Todo")).toBeVisible();

  const otherPage = await browser.newPage();
  await register(otherPage, uniqueEmail("other"));
  await expect(otherPage.getByText("Private E2E Todo")).not.toBeVisible();

  await ownerContext.close();
});
