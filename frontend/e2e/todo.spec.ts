import { expect, test, type Page } from "@playwright/test";

const password = "Password@123";

async function register(page: Page, email: string) {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByText("My Todos", { exact: true })).toBeVisible();
}

async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page.getByText("My Todos", { exact: true })).toBeVisible();
}

async function createTodo(page: Page, title: string, description?: string) {
  await page.getByRole("button", { name: "Add Todo" }).click();
  const dialog = page.getByRole("dialog");
  await dialog.getByLabel("Title").fill(title);
  if (description) {
    await dialog.getByLabel("Description (optional)").fill(description);
  }
  await dialog.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}

test("full user journey: register, login, create, toggle, and logout", async ({
  page,
}) => {
  const stamp = Date.now();
  const email = `journey-${stamp}@example.com`;
  const title = `E2E todo ${stamp}`;

  await register(page, email);
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);

  await login(page, email);
  await createTodo(page, title, "Created by Playwright");

  const todoCheckbox = page.getByRole("checkbox", { name: title });
  await todoCheckbox.click();
  await expect(todoCheckbox).toBeChecked();

  await page.reload();
  await expect(page.getByRole("checkbox", { name: title })).toBeChecked();

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect(page.getByRole("heading", { name: "Welcome Back" })).toBeVisible();
});

test("cross-user isolation: another session cannot see a private todo", async ({
  browser,
}) => {
  const stamp = Date.now();
  const privateTitle = `User A private ${stamp}`;
  const contextA = await browser.newContext();
  const contextB = await browser.newContext();

  try {
    const pageA = await contextA.newPage();
    await register(pageA, `user-a-${stamp}@example.com`);
    await createTodo(pageA, privateTitle);
    await expect(pageA.getByText(privateTitle, { exact: true })).toBeVisible();

    const pageB = await contextB.newPage();
    await register(pageB, `user-b-${stamp}@example.com`);
    await expect(pageB.getByText(privateTitle, { exact: true })).toHaveCount(0);
    await expect(pageB.getByText("No todos yet")).toBeVisible();
  } finally {
    await contextA.close();
    await contextB.close();
  }
});
