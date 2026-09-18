import { expect, test } from "@playwright/test";

const password = "Password@123";
const uniqueEmail = (prefix: string) =>
  `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}@example.com`;

async function register(page: import("@playwright/test").Page, email: string) {
  await page.goto("/register");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page.getByText("My Todos", { exact: true })).toBeVisible();
}

test("user can create, toggle, reload, and log out", async ({ page }) => {
  const title = `E2E todo ${Date.now()}`;
  await register(page, uniqueEmail("journey"));

  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Create" }).click();
  const checkbox = page.getByRole("checkbox", { name: title });
  await expect(checkbox).toBeVisible();
  await checkbox.click();
  await expect(checkbox).toBeChecked();
  await page.reload();
  await expect(page.getByRole("checkbox", { name: title })).toBeChecked();
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
});

test("a second user cannot see another user's private todo", async ({ browser }) => {
  const title = `Private E2E todo ${Date.now()}`;
  const userAContext = await browser.newContext();
  const userAPage = await userAContext.newPage();
  await register(userAPage, uniqueEmail("user-a"));
  await userAPage.getByRole("button", { name: "Add Todo" }).click();
  await userAPage.getByLabel("Title").fill(title);
  await userAPage.getByRole("button", { name: "Create" }).click();
  await expect(userAPage.getByText(title)).toBeVisible();

  const userBContext = await browser.newContext();
  const userBPage = await userBContext.newPage();
  await register(userBPage, uniqueEmail("user-b"));
  await expect(userBPage.getByText(title)).toHaveCount(0);

  await userAContext.close();
  await userBContext.close();
});
