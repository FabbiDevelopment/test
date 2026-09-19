import { expect, test } from "@playwright/test";

import { E2E_API_BASE_URL, e2eAccount } from "./fixtures/test-data";

interface TokenResponse {
  access_token: string;
}

interface TodoListResponse {
  items: Array<{ id: string; title: string }>;
  total: number;
  page: number;
  size: number;
}

test("shows Todos beyond the first page and resets pagination when filtering", async (
  { page, request },
  testInfo,
) => {
  const healthResponse = await request.get(`${E2E_API_BASE_URL}/health`);
  expect(healthResponse.ok()).toBeTruthy();

  const account = e2eAccount("pagination", testInfo.retry);
  const registerResponse = await request.post(
    `${E2E_API_BASE_URL}/api/v1/auth/register`,
    { data: account },
  );
  let tokens: TokenResponse;
  if (registerResponse.status() === 201) {
    tokens = (await registerResponse.json()) as TokenResponse;
  } else {
    // The source allowlist resets this account before each suite. This fallback
    // also makes a direct rerun safe when the running backend image predates a
    // newly added fixture identity.
    expect(registerResponse.status()).toBe(400);
    const loginResponse = await request.post(`${E2E_API_BASE_URL}/api/v1/auth/login`, {
      data: account,
    });
    expect(loginResponse.status()).toBe(200);
    tokens = (await loginResponse.json()) as TokenResponse;
  }
  const headers = { Authorization: `Bearer ${tokens.access_token}` };

  while (true) {
    const listResponse = await request.get(
      `${E2E_API_BASE_URL}/api/v1/todos?page=1&size=100`,
      { headers },
    );
    expect(listResponse.status()).toBe(200);
    const existingTodos = (await listResponse.json()) as TodoListResponse;
    if (existingTodos.items.length === 0) {
      break;
    }

    for (const todo of existingTodos.items) {
      const deleteResponse = await request.delete(
        `${E2E_API_BASE_URL}/api/v1/todos/${todo.id}`,
        { headers },
      );
      expect(deleteResponse.status()).toBe(204);
    }
  }

  for (let number = 1; number <= 101; number += 1) {
    const createResponse = await request.post(`${E2E_API_BASE_URL}/api/v1/todos`, {
      headers,
      data: { title: `Pagination Todo ${number}` },
    });
    expect(createResponse.status()).toBe(201);
  }

  await page.goto("/login");
  await page.getByLabel("Email").fill(account.email);
  await page.getByLabel("Password").fill(account.password);
  await page.getByRole("button", { name: "Sign In" }).click();
  await expect(page).toHaveURL(/\/$/);

  await expect(page.getByRole("navigation", { name: "Todo pagination" })).toBeVisible();
  await expect(page.getByText("Showing 1–100 of 101 todos")).toBeVisible();
  await expect(page.getByText("Page 1 of 2")).toBeVisible();
  await expect(page.getByRole("button", { name: "Previous page" })).toBeDisabled();

  const secondPageResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos?") &&
      new URL(response.url()).searchParams.get("page") === "2",
  );
  await page.getByRole("button", { name: "Next page" }).click();
  const secondPageResponse = await secondPageResponsePromise;
  expect(secondPageResponse.status()).toBe(200);
  const secondPage = (await secondPageResponse.json()) as TodoListResponse;
  expect(secondPage).toMatchObject({ total: 101, page: 2, size: 100 });
  expect(secondPage.items).toHaveLength(1);
  await expect(page.getByText("Showing 101–101 of 101 todos")).toBeVisible();
  await expect(page.getByText("Page 2 of 2")).toBeVisible();
  await expect(page.getByText(secondPage.items[0].title, { exact: true })).toBeVisible();

  await page.getByLabel("Find work").fill("Pagination Todo");
  const filteredPageResponsePromise = page.waitForResponse(
    (response) =>
      response.url().includes("/api/v1/todos?") &&
      new URL(response.url()).searchParams.get("page") === "1" &&
      new URL(response.url()).searchParams.get("keyword") === "Pagination Todo",
  );
  await page.getByRole("button", { name: "Apply filters" }).click();
  expect((await filteredPageResponsePromise).status()).toBe(200);
  await expect(page.getByText("Page 1 of 2")).toBeVisible();
});
