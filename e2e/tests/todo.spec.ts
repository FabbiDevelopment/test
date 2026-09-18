import { expect, test, type Page } from "@playwright/test";

const password = "Password@123";

function uniqueEmail(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(16).slice(2)}@test.com`;
}

async function register(page: Page, email: string): Promise<void> {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: /create account/i }).click();
  await expect(page).toHaveURL("/");
}

async function createTodo(page: Page, title: string): Promise<void> {
  await page.getByRole("button", { name: /add todo/i }).click();
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}

test("register, create, toggle, verify, and logout", async ({ page }) => {
  await register(page, uniqueEmail("journey"));
  const title = `Journey todo ${Date.now()}`;
  await createTodo(page, title);

  const checkbox = page.getByRole("checkbox", { name: title });
  await checkbox.click();
  await expect(checkbox).toBeChecked();

  await page.reload();
  await expect(page.getByRole("checkbox", { name: title })).toBeChecked();
  await page.getByRole("button", { name: /logout/i }).click();
  await expect(page).toHaveURL("/login");
});

test("todos remain isolated between users", async ({ browser }) => {
  const ownerContext = await browser.newContext();
  const otherContext = await browser.newContext();
  const ownerPage = await ownerContext.newPage();
  const otherPage = await otherContext.newPage();
  const privateTitle = `Private ${Date.now()}`;

  await register(ownerPage, uniqueEmail("owner"));
  await createTodo(ownerPage, privateTitle);
  await register(otherPage, uniqueEmail("other"));

  await expect(otherPage.getByText(privateTitle, { exact: true })).toHaveCount(0);

  await ownerContext.close();
  await otherContext.close();
});
