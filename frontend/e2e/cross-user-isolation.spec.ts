import { expect, test, type APIRequestContext, type Page } from "@playwright/test";

import {
  E2E_API_BASE_URL,
  e2eAccount,
  e2eTodoTitle,
} from "./fixtures/test-data";

interface TokenResponse {
  access_token: string;
}

interface TodoResponse {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
}

async function registerUser(
  request: APIRequestContext,
  email: string,
  password: string,
): Promise<TokenResponse> {
  const response = await request.post(`${E2E_API_BASE_URL}/api/v1/auth/register`, {
    data: { email, password },
  });
  expect(response.status()).toBe(201);
  return (await response.json()) as TokenResponse;
}

async function login(page: Page, email: string, password: string) {
  await page.goto("/login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);

  const loginResponsePromise = page.waitForResponse(
    (response) =>
      response.url().endsWith("/api/v1/auth/login") &&
      response.request().method() === "POST",
  );
  const listResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos?") &&
      response.request().method() === "GET",
  );

  await page.getByRole("button", { name: "Sign In" }).click();
  expect((await loginResponsePromise).status()).toBe(200);
  await expect(page).toHaveURL(/\/$/);
  await expect(page.getByText(email)).toBeVisible();

  return listResponsePromise;
}

test("prevents user B from viewing or mutating user A's Todo", async ({
  baseURL,
  browser,
  request,
}, testInfo) => {
  if (!baseURL) {
    throw new Error("Playwright baseURL must be configured for Journey 2");
  }

  const healthResponse = await request.get(`${E2E_API_BASE_URL}/health`);
  expect(
    healthResponse.ok(),
    `Start the backend on ${E2E_API_BASE_URL} before running Journey 2`,
  ).toBeTruthy();

  const userA = e2eAccount("journey2-a", testInfo.retry);
  const userB = e2eAccount("journey2-b", testInfo.retry);
  const todoTitle = e2eTodoTitle(2, testInfo.retry);
  const todoDescription = "This Todo must remain private to user A";

  const [userATokens] = await Promise.all([
    registerUser(request, userA.email, userA.password),
    registerUser(request, userB.email, userB.password),
  ]);

  const [userAContext, userBContext] = await Promise.all([
    browser.newContext({ baseURL }),
    browser.newContext({ baseURL }),
  ]);
  const userAPage = await userAContext.newPage();
  const userBPage = await userBContext.newPage();

  let todoId: string | undefined;

  try {
    await login(userAPage, userA.email, userA.password);

    await userAPage.getByRole("button", { name: "Add Todo" }).click();
    const createDialog = userAPage.getByRole("dialog", {
      name: "Create Todo",
    });
    await createDialog.getByLabel("Title").fill(todoTitle);
    await createDialog
      .getByLabel("Description (optional)")
      .fill(todoDescription);

    const createResponsePromise = userAPage.waitForResponse(
      (response) =>
        response.url().endsWith("/api/v1/todos") &&
        response.request().method() === "POST",
    );
    await createDialog.getByRole("button", { name: "Create" }).click();
    const createResponse = await createResponsePromise;
    expect(createResponse.status()).toBe(201);
    const createdTodo = (await createResponse.json()) as TodoResponse;
    todoId = createdTodo.id;

    const userATodo = userAPage
      .getByTestId("todo-item")
      .filter({ hasText: todoTitle });
    await expect(userATodo).toContainText(todoDescription);

    const userBListResponse = await login(
      userBPage,
      userB.email,
      userB.password,
    );
    expect(userBListResponse.status()).toBe(200);
    const userBList = (await userBListResponse.json()) as {
      items: TodoResponse[];
    };
    expect(userBList.items).not.toContainEqual(
      expect.objectContaining({ id: todoId }),
    );
    await expect(userBPage.getByText(todoTitle, { exact: true })).toHaveCount(
      0,
    );
    await expect(userBPage.getByText("No todos yet")).toBeVisible();

    const userBAccessToken = await userBPage.evaluate(() =>
      localStorage.getItem("access_token"),
    );
    expect(userBAccessToken).not.toBeNull();
    const userBHeaders = {
      Authorization: `Bearer ${userBAccessToken}`,
    };

    const forbiddenRead = await request.get(
      `${E2E_API_BASE_URL}/api/v1/todos/${todoId}`,
      { headers: userBHeaders },
    );
    expect(forbiddenRead.status()).toBe(404);

    const forbiddenUpdate = await request.put(
      `${E2E_API_BASE_URL}/api/v1/todos/${todoId}`,
      {
        headers: userBHeaders,
        data: { title: "Compromised by user B", completed: true },
      },
    );
    expect(forbiddenUpdate.status()).toBe(404);

    const forbiddenDelete = await request.delete(
      `${E2E_API_BASE_URL}/api/v1/todos/${todoId}`,
      { headers: userBHeaders },
    );
    expect(forbiddenDelete.status()).toBe(404);

    const ownerRead = await request.get(
      `${E2E_API_BASE_URL}/api/v1/todos/${todoId}`,
      {
        headers: { Authorization: `Bearer ${userATokens.access_token}` },
      },
    );
    expect(ownerRead.status()).toBe(200);
    expect((await ownerRead.json()) as TodoResponse).toMatchObject({
      id: todoId,
      title: todoTitle,
      description: todoDescription,
      completed: false,
    });

    await userAPage.reload();
    const unchangedUserATodo = userAPage
      .getByTestId("todo-item")
      .filter({ hasText: todoTitle });
    await expect(unchangedUserATodo).toContainText(todoDescription);
    await expect(unchangedUserATodo.getByText("Active", { exact: true })).toBeVisible();
  } finally {
    if (todoId) {
      await request.delete(`${E2E_API_BASE_URL}/api/v1/todos/${todoId}`, {
        headers: { Authorization: `Bearer ${userATokens.access_token}` },
      });
    }
    await Promise.all([userAContext.close(), userBContext.close()]);
  }
});
