import { randomUUID } from "node:crypto";
import { expect, test as base, type Page } from "@playwright/test";

const apiUrl = `${(process.env.VITE_API_URL || "http://localhost:8000").replace(/\/$/, "")}/api/v1`;

interface Account {
  email: string;
  password: string;
}

interface Todo {
  id: string;
  title: string;
  description: string;
  completed: boolean;
}

interface CreatedTodo {
  id: string;
  account: Account;
}

const test = base.extend<{ createdTodos: CreatedTodo[] }>({
  createdTodos: async ({ request }, runTest) => {
    const todos: CreatedTodo[] = [];
    await runTest(todos);
    // Only remove todos created by this test; leave existing user data intact.
    for (const todo of todos) {
      const login = await request.post(`${apiUrl}/auth/login`, { data: todo.account });
      expect(login.ok(), "Test account must be able to log in for cleanup").toBe(true);
      const { access_token } = await login.json();
      const deleted = await request.delete(`${apiUrl}/todos/${todo.id}`, {
        headers: { Authorization: `Bearer ${access_token}` },
      });
      expect([204, 404]).toContain(deleted.status());
    }
  },
});

test.describe.configure({ timeout: 60_000 });

function newAccount(): Account {
  return { email: `e2e-${randomUUID()}@example.com`, password: "E2ePassword123!" };
}

function apiResponse(page: Page, path: string, method: string) {
  return page.waitForResponse((response) =>
    new URL(response.url()).pathname === `/api/v1${path}` &&
    response.request().method() === method
  );
}

async function register(page: Page, account: Account) {
  await page.goto("/register");
  await page.getByLabel("Email", { exact: true }).fill(account.email);
  await page.getByLabel("Password", { exact: true }).fill(account.password);
  await page.getByLabel("Confirm Password", { exact: true }).fill(account.password);
  const registered = apiResponse(page, "/auth/register", "POST");
  await page.getByRole("button", { name: "Create Account", exact: true }).click();
  expect((await registered).status()).toBe(201);
  await expect(page).toHaveURL("/");
  await expect(page.getByText(account.email, { exact: true })).toBeVisible();
  await expect(page.getByText("No todos yet", { exact: true })).toBeVisible();
}

async function login(page: Page, account: Account) {
  await page.getByLabel("Email", { exact: true }).fill(account.email);
  await page.getByLabel("Password", { exact: true }).fill(account.password);
  const loggedIn = apiResponse(page, "/auth/login", "POST");
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  expect((await loggedIn).status()).toBe(200);
  await expect(page).toHaveURL("/");
  await expect(page.getByText(account.email, { exact: true })).toBeVisible();
}

async function logout(page: Page) {
  const loggedOut = apiResponse(page, "/auth/logout", "POST");
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  expect((await loggedOut).status()).toBe(200);
  await expect(page).toHaveURL("/login");
  expect(await page.evaluate(() => [
    localStorage.getItem("access_token"), localStorage.getItem("refresh_token"),
  ])).toEqual([null, null]);
}

async function createTodo(
  page: Page, account: Account, createdTodos: CreatedTodo[], title: string,
) {
  const description = `Private details for ${title}`;
  await page.getByRole("button", { name: "Add Todo", exact: true }).click();
  await page.getByLabel("Title", { exact: true }).fill(title);
  await page.getByLabel("Description (optional)", { exact: true }).fill(description);
  const created = apiResponse(page, "/todos", "POST");
  await page.getByRole("button", { name: "Create", exact: true }).click();
  const response = await created;
  expect(response.status()).toBe(201);
  const todo: Todo = await response.json();
  createdTodos.push({ id: todo.id, account });
  expect(todo).toMatchObject({ title, description, completed: false });
  await expect(page.getByRole("checkbox", { name: title, exact: true })).not.toBeChecked();
  await expect(page.getByText(description, { exact: true })).toBeVisible();
  return todo;
}

async function toggleAndVerifyPersistence(page: Page, todo: Todo, completed: boolean) {
  const updated = apiResponse(page, `/todos/${todo.id}`, "PUT");
  await page.getByRole("checkbox", { name: todo.title, exact: true }).click();
  const response = await updated;
  expect(response.status()).toBe(200);
  expect(await response.json()).toMatchObject({
    completed, title: todo.title, description: todo.description,
  });
  // Reload discards the optimistic cache and confirms the state from the API.
  await page.reload();
  const checkbox = page.getByRole("checkbox", { name: todo.title, exact: true });
  if (completed) await expect(checkbox).toBeChecked();
  else await expect(checkbox).not.toBeChecked();
  await expect(page.getByText(todo.description, { exact: true })).toBeVisible();
}

test.beforeAll(async ({ request }) => {
  const healthUrl = new URL("/health", apiUrl).toString();
  const response = await request.get(healthUrl);
  expect(response.ok(), "Start backend, PostgreSQL and Redis before running backend-e2e").toBe(true);
});

test("full user journey: register, login, create, toggle, verify and logout", async ({ page, createdTodos }) => {
  const account = newAccount();
  await register(page, account);
  await logout(page);
  await login(page, account);
  const todo = await createTodo(page, account, createdTodos, `Journey ${randomUUID()}`);
  await toggleAndVerifyPersistence(page, todo, true);
  await toggleAndVerifyPersistence(page, todo, false);
  await logout(page);
  await page.goto("/");
  await expect(page).toHaveURL("/login");
});

test("separate user sessions cannot see each other's private todos", async ({ page: pageA, browser, baseURL, createdTodos }) => {
  const accountA = newAccount();
  const accountB = newAccount();
  await register(pageA, accountA);
  const todoA = await createTodo(pageA, accountA, createdTodos, `Private A ${randomUUID()}`);

  // B uses independent cookies, localStorage and React Query cache.
  const contextB = await browser.newContext({ baseURL });
  try {
    const pageB = await contextB.newPage();
    await register(pageB, accountB);
    await logout(pageB);
    await login(pageB, accountB);
    await expect(pageB.getByText("No todos yet", { exact: true })).toBeVisible();
    await expect(pageB.getByText(todoA.title, { exact: true })).toHaveCount(0);
    await expect(pageB.getByText(todoA.description, { exact: true })).toHaveCount(0);
    const todoB = await createTodo(pageB, accountB, createdTodos, `Private B ${randomUUID()}`);

    await pageB.reload();
    await expect(pageB.getByText(accountB.email, { exact: true })).toBeVisible();
    await expect(pageB.getByRole("checkbox", { name: todoB.title, exact: true })).toBeVisible();
    await expect(pageB.getByText(todoA.title, { exact: true })).toHaveCount(0);
    await expect(pageB.getByText(todoA.description, { exact: true })).toHaveCount(0);

    await pageA.reload();
    await expect(pageA.getByText(accountA.email, { exact: true })).toBeVisible();
    await expect(pageA.getByRole("checkbox", { name: todoA.title, exact: true })).toBeVisible();
    await expect(pageA.getByText(todoB.title, { exact: true })).toHaveCount(0);
    await logout(pageB);
    await logout(pageA);
  } finally {
    await contextB.close();
  }
});
