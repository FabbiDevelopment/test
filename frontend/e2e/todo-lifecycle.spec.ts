import { expect, test } from "@playwright/test";

import {
  E2E_API_BASE_URL,
  e2eAccount,
  e2eTodoTitle,
} from "./fixtures/test-data";

test("registers, logs in, and completes the Todo lifecycle", async ({
  page,
  request,
}, testInfo) => {
  const healthResponse = await request.get(`${E2E_API_BASE_URL}/health`);
  expect(
    healthResponse.ok(),
    `Start the backend on ${E2E_API_BASE_URL} before running Journey 1`,
  ).toBeTruthy();

  const account = e2eAccount("journey1", testInfo.retry);
  const initialTitle = e2eTodoTitle(1, testInfo.retry);
  const initialDescription = "Created by the Playwright lifecycle journey";
  const updatedTitle = `${initialTitle} updated`;
  const updatedDescription = "Edited before marking the Todo complete";

  await page.goto("/register");
  await page.getByLabel("Email").fill(account.email);
  await page.getByLabel("Password", { exact: true }).fill(account.password);
  await page.getByLabel("Confirm Password").fill(account.password);

  const registerResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/auth/register") &&
      response.request().method() === "POST",
  );
  const initialTodoListResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos?") &&
      response.request().method() === "GET",
  );
  await page.getByRole("button", { name: "Create Account" }).click();
  expect((await registerResponsePromise).status()).toBe(201);

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByRole("heading", { name: "Todo App" })).toBeVisible();
  await expect(page.getByText(account.email)).toBeVisible();
  const initialTodoListResponse = await initialTodoListResponsePromise;
  expect(initialTodoListResponse.status()).toBe(200);
  expect(new URL(initialTodoListResponse.url()).searchParams.get("size")).toBe(
    "100",
  );

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);

  await page.getByLabel("Email").fill(account.email);
  await page.getByLabel("Password").fill(account.password);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/auth/login") &&
      response.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Sign In" }).click();
  expect((await loginResponsePromise).status()).toBe(200);

  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText(account.email)).toBeVisible();

  await page.getByRole("button", { name: "Add Todo" }).click();
  const createDialog = page.getByRole("dialog", { name: "Create Todo" });
  await createDialog.getByLabel("Title").fill(initialTitle);
  await createDialog
    .getByLabel("Description (optional)")
    .fill(initialDescription);

  const createResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/todos") &&
      response.request().method() === "POST",
  );
  await createDialog.getByRole("button", { name: "Create" }).click();
  const createResponse = await createResponsePromise;
  expect(createResponse.status()).toBe(201);
  const createdTodoResponse = (await createResponse.json()) as { id: string };

  const createdTodo = page
    .getByTestId("todo-item")
    .filter({ hasText: initialTitle });
  await expect(createdTodo).toContainText(initialDescription);

  await createdTodo
    .getByRole("button", { name: `Edit ${initialTitle}` })
    .click();
  const editDialog = page.getByRole("dialog", { name: "Edit Todo" });
  await editDialog.getByLabel("Title").fill(updatedTitle);
  await editDialog
    .getByLabel("Description (optional)")
    .fill(updatedDescription);

  const editResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos/") &&
      response.request().method() === "PUT",
  );
  await editDialog.getByRole("button", { name: "Save" }).click();
  expect((await editResponsePromise).status()).toBe(200);

  const updatedTodo = page
    .getByTestId("todo-item")
    .filter({ hasText: updatedTitle });
  await expect(updatedTodo).toContainText(updatedDescription);
  await expect(page.getByText(initialTitle, { exact: true })).toHaveCount(0);

  const completeResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos/") &&
      response.request().method() === "PUT",
  );
  await updatedTodo.getByRole("button", { name: `Mark ${updatedTitle} as completed` }).click();
  expect((await completeResponsePromise).status()).toBe(200);
  await expect(updatedTodo.getByText("Completed", { exact: true })).toBeVisible();

  const deleteResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos/") &&
      response.request().method() === "DELETE",
  );
  await updatedTodo
    .getByRole("button", { name: `Delete ${updatedTitle}` })
    .click();
  expect((await deleteResponsePromise).status()).toBe(204);

  await expect(updatedTodo).toHaveCount(0);
  await expect(page.getByText("No todos yet")).toBeVisible();

  const accessToken = await page.evaluate(() =>
    localStorage.getItem("access_token"),
  );
  expect(accessToken).not.toBeNull();
  const deletedTodoResponse = await request.get(
    `${E2E_API_BASE_URL}/api/v1/todos/${createdTodoResponse.id}`,
    {
      headers: { Authorization: `Bearer ${accessToken}` },
    },
  );
  expect(deletedTodoResponse.status()).toBe(404);

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL(/\/login$/);
  await expect
    .poll(() =>
      page.evaluate(() => ({
        accessToken: localStorage.getItem("access_token"),
        refreshToken: localStorage.getItem("refresh_token"),
      })),
    )
    .toEqual({ accessToken: null, refreshToken: null });
});
