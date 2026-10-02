import { expect, test, type Page } from "@playwright/test";

type UserKey = "a" | "b";

interface MockOptions {
  logoutFails?: boolean;
  delayList?: boolean;
  delayUpdate?: boolean;
  updateUnauthorized?: boolean;
}

async function mockApi(page: Page, options: MockOptions = {}) {
  const state = {
    listReads: { a: 0, b: 0 },
    profileReads: { a: 0, b: 0 },
    updateStarted: false,
  };
  const todos = {
    a: [{ id: "todo-a", title: "Private A", description: "Details A", completed: false, user_id: "user-a" }],
    b: [{ id: "todo-b", title: "Private B", description: "Details B", completed: false, user_id: "user-b" }],
  };
  let releaseList!: () => void;
  let releaseUpdate!: () => void;
  const listGate = new Promise<void>((resolve) => { releaseList = resolve; });
  const updateGate = new Promise<void>((resolve) => { releaseUpdate = resolve; });
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "*",
    "Access-Control-Allow-Methods": "*",
  };

  // User-specific responses isolate frontend cache behavior from backend Redis.
  await page.route("**/api/v1/**", async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    const method = request.method();
    const user: UserKey = request.headers().authorization === "Bearer token-b" ? "b" : "a";
    const respond = (data: unknown, status = 200) => route.fulfill({
      status, headers, contentType: "application/json", body: JSON.stringify(data),
    });
    if (method === "OPTIONS") return route.fulfill({ status: 204, headers });
    if (path.endsWith("/auth/login") || path.endsWith("/auth/register")) {
      const account = request.postDataJSON().email.startsWith("b@") ? "b" : "a";
      return respond({ access_token: `token-${account}`, refresh_token: `refresh-${account}`, token_type: "bearer" });
    }
    if (path.endsWith("/auth/logout")) {
      return respond({ message: "Logged out" }, options.logoutFails ? 503 : 200);
    }
    if (path.endsWith("/auth/me")) {
      state.profileReads[user] += 1;
      return respond({ id: `user-${user}`, email: `${user}@example.com`, created_at: "2026-10-02T00:00:00Z" });
    }
    if (path.endsWith("/todos") && method === "GET") {
      state.listReads[user] += 1;
      if (options.delayList && user === "a" && state.listReads.a === 1) {
        await listGate;
        if (request.failure()) return;
      }
      return respond({ items: todos[user], total: todos[user].length, page: 1, size: 10000 });
    }
    if (path.endsWith("/todos") && method === "POST") {
      const data = request.postDataJSON();
      const todo = { id: `created-${user}`, title: data.title, description: data.description, completed: false, user_id: `user-${user}` };
      todos[user].push(todo);
      return respond(todo, 201);
    }
    if (method === "PUT") {
      state.updateStarted = true;
      if (options.delayUpdate) await updateGate;
      if (options.updateUnauthorized) return respond({ detail: "Expired token" }, 401);
      Object.assign(todos[user][0], request.postDataJSON());
      return respond(todos[user][0]);
    }
    return respond({ detail: "Unexpected request" }, 404);
  });
  return { listReads: state.listReads, profileReads: state.profileReads, state, releaseList, releaseUpdate };
}

async function login(page: Page, user: UserKey) {
  await page.getByLabel("Email", { exact: true }).fill(`${user}@example.com`);
  await page.getByLabel("Password", { exact: true }).fill("password123");
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await expect(page).toHaveURL("/");
}

async function logout(page: Page) {
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL("/login");
  const tokens = await page.evaluate(() => [
    localStorage.getItem("access_token"), localStorage.getItem("refresh_token"),
  ]);
  expect(tokens).toEqual([null, null]);
}

async function expectUserB(page: Page) {
  await expect(page.getByText("b@example.com", { exact: true })).toBeVisible();
  await expect(page.getByText("Private B", { exact: true })).toBeVisible();
  await expect(page.getByText("Private A", { exact: true })).toHaveCount(0);
  await expect(page.getByText("a@example.com", { exact: true })).toHaveCount(0);
}

for (const logoutFails of [false, true]) {
  test(`switching accounts isolates cached data (logout failure: ${logoutFails})`, async ({ page }) => {
    const state = await mockApi(page, { logoutFails });
    await page.goto("/login");
    await login(page, "a");
    await expect(page.getByText("Private A", { exact: true })).toBeVisible();
    await logout(page);
    await login(page, "b");
    await expectUserB(page);
    expect(state.listReads.b).toBe(1);
    expect(state.profileReads.b).toBe(1);

    // Mutations must invalidate B's newly scoped cache and still update the UI.
    await page.getByRole("button", { name: "Add Todo" }).click();
    await page.getByLabel("Title", { exact: true }).fill("Created by B");
    await page.getByLabel("Description (optional)", { exact: true }).fill("New details");
    await page.getByRole("button", { name: "Create", exact: true }).click();
    await expect(page.getByText("Created by B", { exact: true })).toBeVisible();
    await page.getByRole("checkbox").first().click();
    await expect.poll(() => state.listReads.b).toBeGreaterThanOrEqual(3);
    await expect(page.getByRole("checkbox").first()).toHaveAttribute("aria-checked", "true");
  });
}

test("registering a new account does not reuse the previous account's cache", async ({ page }) => {
  await mockApi(page);
  await page.goto("/login");
  await login(page, "a");
  await expect(page.getByText("Private A", { exact: true })).toBeVisible();
  await logout(page);
  await page.getByRole("link", { name: "Sign up", exact: true }).click();
  await page.getByLabel("Email", { exact: true }).fill("b@example.com");
  await page.getByLabel("Password", { exact: true }).fill("password123");
  await page.getByLabel("Confirm Password", { exact: true }).fill("password123");
  await page.getByRole("button", { name: "Create Account", exact: true }).click();
  await expect(page).toHaveURL("/");
  await expectUserB(page);
});

test("a delayed list response from the previous session cannot replace B's data", async ({ page }) => {
  const state = await mockApi(page, { delayList: true });
  await page.goto("/login");
  await login(page, "a");
  await expect.poll(() => state.listReads.a).toBe(1);
  const cancelled = page.waitForEvent("requestfailed", (request) =>
    request.method() === "GET" && new URL(request.url()).pathname.endsWith("/todos")
  );
  await logout(page);
  await cancelled;
  await login(page, "b");
  await expectUserB(page);
  state.releaseList();
  await expectUserB(page);
});

for (const updateUnauthorized of [false, true]) {
  test(`a late mutation from A cannot affect B's session (401: ${updateUnauthorized})`, async ({ page }) => {
    const state = await mockApi(page, { delayUpdate: true, updateUnauthorized });
    await page.goto("/login");
    await login(page, "a");
    await expect(page.getByText("Private A", { exact: true })).toBeVisible();
    await page.getByRole("checkbox").click();
    await expect.poll(() => state.state.updateStarted).toBe(true);
    await logout(page);
    await login(page, "b");
    await expectUserB(page);
    const response = page.waitForResponse((response) => response.request().method() === "PUT");
    state.releaseUpdate();
    await response;
    // Flush rendering after the late response's callbacks have run.
    await page.evaluate(() => new Promise<void>((resolve) => {
      requestAnimationFrame(() => requestAnimationFrame(() => resolve()));
    }));
    await expect(page).toHaveURL("/");
    await expectUserB(page);
    expect(await page.evaluate(() => localStorage.getItem("access_token"))).toBe("token-b");
    expect(state.listReads.b).toBe(1);
  });
}
