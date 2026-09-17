import { expect, test } from "@playwright/test";

function account(prefix: string) {
  const id = `${Date.now()}-${Math.random().toString(16).slice(2)}`;
  return {
    email: `${prefix}-${id}@example.com`,
    password: "Password123!",
  };
}

async function register(page: import("@playwright/test").Page, email: string, password: string) {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/\/$/);
}

test("register, create, toggle, verify and logout", async ({ page }) => {
  const user = account("journey");
  await register(page, user.email, user.password);

  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill("E2E private todo");
  await page.getByLabel("Description (optional)").fill("Created by Playwright");
  await page.getByRole("button", { name: "Create" }).click();

  const todo = page.getByText("E2E private todo");
  await expect(todo).toBeVisible();
  const todoRow = todo.locator("xpath=../..");
  await todoRow.getByRole("checkbox").click();
  await expect(todo).toHaveClass(/line-through/);
  await todoRow.getByRole("checkbox").click();
  await expect(todo).not.toHaveClass(/line-through/);

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("does not expose User A todo to User B", async ({ browser }) => {
  const userA = account("owner");
  const userB = account("other");
  const ownerContext = await browser.newContext();
  const ownerPage = await ownerContext.newPage();
  await register(ownerPage, userA.email, userA.password);
  await ownerPage.getByRole("button", { name: "Add Todo" }).click();
  await ownerPage.getByLabel("Title").fill("User A private todo");
  await ownerPage.getByRole("button", { name: "Create" }).click();
  await expect(ownerPage.getByText("User A private todo")).toBeVisible();

  const otherContext = await browser.newContext();
  const otherPage = await otherContext.newPage();
  await register(otherPage, userB.email, userB.password);
  await expect(otherPage.getByText("User A private todo")).toHaveCount(0);

  await ownerContext.close();
  await otherContext.close();
});
