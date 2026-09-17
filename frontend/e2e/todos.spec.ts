import { test, expect } from "@playwright/test";

test.describe("Todo E2E Tests", () => {
  const timestamp = Date.now();
  const userAEmail = `user_a_${timestamp}@example.com`;
  const userBEmail = `user_b_${timestamp}@example.com`;
  const password = "Password@123";

  test("Scenario 1: Full User Journey (Register -> Create Todo -> Toggle -> Logout)", async ({ page }) => {
    // 1. Go to Register page
    await page.goto("/register");
    await page.fill('input[type="email"]', userAEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL("/dashboard");
    await expect(page.locator("text=My Todos")).toBeVisible();

    // 2. Create a Todo
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[name="title"]', "E2E Created Todo");
    await page.fill('textarea[name="description"]', "Description for E2E Todo");
    await page.click('button[type="submit"]');

    // Verify item in UI
    await expect(page.locator("text=E2E Created Todo")).toBeVisible();

    // 3. Toggle completion
    const checkbox = page.locator('input[type="checkbox"]').first();
    await checkbox.click();

    // 4. Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL("/login");
  });

  test("Scenario 2: Cross-User Data Isolation", async ({ browser }) => {
    // Session A: User A creates a todo
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    await pageA.goto("/register");
    await pageA.fill('input[type="email"]', userAEmail);
    await pageA.fill('input[type="password"]', password);
    await pageA.click('button[type="submit"]');
    await expect(pageA).toHaveURL("/dashboard");

    await pageA.click('button:has-text("Add Todo")');
    await pageA.fill('input[name="title"]', "User A Private Todo");
    await pageA.click('button[type="submit"]');
    await expect(pageA.locator("text=User A Private Todo")).toBeVisible();

    // Session B: User B logs in on another session
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    await pageB.goto("/register");
    await pageB.fill('input[type="email"]', userBEmail);
    await pageB.fill('input[type="password"]', password);
    await pageB.click('button[type="submit"]');
    await expect(pageB).toHaveURL("/dashboard");

    // User B MUST NOT see User A's private todo
    await expect(pageB.locator("text=User A Private Todo")).not.toBeVisible();

    await contextA.close();
    await contextB.close();
  });
});
