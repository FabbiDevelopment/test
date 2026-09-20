import { test, expect, Browser, BrowserContext, Page } from "@playwright/test";

/**
 * Scenario 2: Cross-User Data Isolation
 *
 * Steps:
 * 1. User A registers and creates a private todo
 * 2. User A logs out
 * 3. User B registers in a fresh browser context (no shared cookies/storage)
 * 4. User B views their todo list
 * 5. Verify User B's list does NOT contain User A's todo
 */

const uniqueEmail = (prefix: string) => `e2e_${prefix}_${Date.now()}@test.com`;

async function registerAndLogin(
  page: Page,
  email: string,
  password: string
): Promise<void> {
  await page.goto("/register");
  await page.getByLabel(/email/i).fill(email);
  await page.getByLabel(/password/i).fill(password);
  await page.getByRole("button", { name: /register|sign up|create account/i }).click();
  await expect(page).toHaveURL("/", { timeout: 10_000 });
}

async function createTodo(page: Page, title: string): Promise<void> {
  await page.getByRole("button", { name: /add todo/i }).click();
  await page.getByLabel(/title/i).fill(title);
  await page.getByRole("button", { name: /save|create|submit|add/i }).click();
  await expect(page.getByText(title)).toBeVisible({ timeout: 8_000 });
}

async function logout(page: Page): Promise<void> {
  await page.getByRole("button", { name: /logout/i }).click();
  await expect(page).toHaveURL(/login/, { timeout: 8_000 });
}

test.describe("Cross-User Data Isolation", () => {
  test("User A's todos are not visible to User B", async ({ browser }) => {
    const password = "Password@123";
    const emailA = uniqueEmail("userA");
    const emailB = uniqueEmail("userB");
    const privateTodoTitle = `UserA Private Todo ${Date.now()}`;

    // ── User A: register, create todo, logout ──────────────────────────────
    const contextA: BrowserContext = await browser.newContext();
    const pageA: Page = await contextA.newPage();

    await registerAndLogin(pageA, emailA, password);
    await createTodo(pageA, privateTodoTitle);

    // Confirm the todo is visible to User A
    await expect(pageA.getByText(privateTodoTitle)).toBeVisible();

    await logout(pageA);
    await contextA.close();

    // ── User B: fresh context (separate session, no shared localStorage) ──
    const contextB: BrowserContext = await browser.newContext();
    const pageB: Page = await contextB.newPage();

    await registerAndLogin(pageB, emailB, password);

    // Wait for todo list to load (allow empty state)
    await expect(pageB.getByText("My Todos")).toBeVisible();

    // Give the page time to finish loading todos
    await pageB.waitForTimeout(2_000);

    // ── Assertion: User B must NOT see User A's todo ───────────────────────
    const privateTodoLocator = pageB.getByText(privateTodoTitle);
    await expect(privateTodoLocator).not.toBeVisible({
      timeout: 5_000,
    });

    // Additional check: User B's todo count should be 0
    const todoItems = pageB.locator('[id^="todo-"]');
    await expect(todoItems).toHaveCount(0, { timeout: 5_000 });

    await logout(pageB);
    await contextB.close();
  });

  test("User A's todos are not accessible via API with User B token", async ({
    request,
  }) => {
    /**
     * API-level isolation test:
     * 1. Register User A via API → create a todo
     * 2. Register User B via API → try to GET User A's todo by ID
     * 3. Must receive 403 Forbidden
     */
    const password = "Password@123";
    const emailA = uniqueEmail("apiA");
    const emailB = uniqueEmail("apiB");
    const API_URL = "http://localhost:8000/api/v1";

    // Register User A
    const regA = await request.post(`${API_URL}/auth/register`, {
      data: { email: emailA, password },
    });
    expect(regA.status()).toBe(201);
    const tokenA = (await regA.json()).access_token;

    // Create a todo as User A
    const createResp = await request.post(`${API_URL}/todos`, {
      data: { title: "User A API Todo" },
      headers: { Authorization: `Bearer ${tokenA}` },
    });
    expect(createResp.status()).toBe(201);
    const todoId = (await createResp.json()).id;

    // Register User B
    const regB = await request.post(`${API_URL}/auth/register`, {
      data: { email: emailB, password },
    });
    expect(regB.status()).toBe(201);
    const tokenB = (await regB.json()).access_token;

    // User B tries to access User A's todo
    const accessResp = await request.get(`${API_URL}/todos/${todoId}`, {
      headers: { Authorization: `Bearer ${tokenB}` },
    });

    expect(accessResp.status()).toBe(403);
  });
});
