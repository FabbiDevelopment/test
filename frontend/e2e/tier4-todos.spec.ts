import { expect, test, type Page } from "@playwright/test";

import { E2E_API_BASE_URL, e2eAccount } from "./fixtures/test-data";

async function createTodo(page: Page, title: string) {
  await page.getByRole("button", { name: "Add Todo" }).click();
  const dialog = page.getByRole("dialog", { name: "Create Todo" });
  await dialog.getByLabel("Title").fill(title);

  const responsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/todos") &&
      response.request().method() === "POST",
  );
  await dialog.getByRole("button", { name: "Create" }).click();
  expect((await responsePromise).status()).toBe(201);
}

test("manages Tags, filters Todos, and bulk-updates selected work", async (
  { page, request },
  testInfo,
) => {
  const healthResponse = await request.get(`${E2E_API_BASE_URL}/health`);
  expect(healthResponse.ok()).toBeTruthy();

  const account = e2eAccount("tier4", testInfo.retry);
  const taggedTitle = `Tier 4 tagged work r${testInfo.retry}`;
  const plainTitle = `Tier 4 plain work r${testInfo.retry}`;
  const tagName = `Client r${testInfo.retry}`;

  await page.goto("/register");
  await page.getByLabel("Email").fill(account.email);
  await page.getByLabel("Password", { exact: true }).fill(account.password);
  await page.getByLabel("Confirm Password").fill(account.password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL(/\/$/);

  await page.getByRole("button", { name: "Manage tags" }).click();
  const tagDialog = page.getByRole("dialog", { name: "Manage tags" });
  await tagDialog.getByLabel("Tag name").fill(tagName);
  await tagDialog.getByLabel("Color (optional)").fill("#16a34a");
  await tagDialog.getByRole("button", { name: "Add" }).click();
  await expect(tagDialog.getByText(tagName, { exact: true })).toBeVisible();
  await tagDialog.getByRole("button", { name: "Close" }).click();

  await createTodo(page, taggedTitle);
  await createTodo(page, plainTitle);
  const taggedTodoRow = page.getByTestId("todo-item").filter({ hasText: taggedTitle });
  await taggedTodoRow.getByRole("button", { name: `Manage tags for ${taggedTitle}` }).click();
  const todoTagDialog = page.getByRole("dialog", { name: `Tags for ${taggedTitle}` });
  const attachResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/tags") &&
      response.request().method() === "POST" &&
      response.request().postDataJSON()?.tag_id,
  );
  await todoTagDialog.getByRole("button", { name: tagName }).click();
  expect((await attachResponsePromise).status()).toBe(204);
  await expect(todoTagDialog.getByRole("button", { name: `Remove ${tagName}` })).toBeVisible();
  await todoTagDialog.getByRole("button", { name: "Close" }).click();
  await expect(taggedTodoRow.getByText(tagName, { exact: true })).toBeVisible();

  const tag = await page.getByLabel("Tag", { exact: true }).locator("option", { hasText: tagName }).getAttribute("value");
  expect(tag).not.toBeNull();
  await page.getByLabel("Tag", { exact: true }).selectOption(tag ?? undefined);
  const filteredResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos?") &&
      response.url().includes(`tag_id=${tag}`),
  );
  await page.getByRole("button", { name: "Apply filters" }).click();
  expect((await filteredResponsePromise).status()).toBe(200);
  await expect(page.getByText(taggedTitle, { exact: true })).toBeVisible();
  await expect(page.getByText(plainTitle, { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Clear filters" }).click();
  await expect(page.getByText(plainTitle, { exact: true })).toBeVisible();

  const plainTodoRow = page.getByTestId("todo-item").filter({ hasText: plainTitle });
  await taggedTodoRow.getByRole("checkbox", { name: "Select for bulk action" }).click();
  await plainTodoRow.getByRole("checkbox", { name: "Select for bulk action" }).click();
  const bulkResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/todos/bulk-status") &&
      response.request().method() === "PATCH",
  );
  await page.getByRole("button", { name: "Mark completed" }).click();
  expect((await bulkResponsePromise).status()).toBe(200);
  await expect(taggedTodoRow.getByText("Completed", { exact: true })).toBeVisible();
  await expect(plainTodoRow.getByText("Completed", { exact: true })).toBeVisible();
});
