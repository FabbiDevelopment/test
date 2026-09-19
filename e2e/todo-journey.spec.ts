import { test, expect } from "@playwright/test";

test.describe("Full-Stack Todo Application E2E Tests", () => {
  test("Scenario 1: Full User Journey (Register -> Create Todo -> Toggle -> Logout)", async ({ page }) => {
    const timestamp = Date.now();
    const userEmail = `user_journey_${timestamp}@example.com`;
    const password = "Password@123";

    // 1. Navigate to Register page
    await page.goto("/register");
    await expect(page).toHaveURL(/.*register/);

    // 2. Register account
    await page.fill("#email", userEmail);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button[type="submit"]');

    // 3. Verify redirected to Todo page
    await expect(page).toHaveURL("/");
    await expect(page.locator("h1")).toContainText("Todo App");
    await expect(page.getByText(userEmail)).toBeVisible();

    // 4. Create a new Todo
    await page.getByRole("button", { name: /Add Todo/i }).click();
    await page.fill("#title", "Buy organic milk");
    await page.fill("#description", "Whole milk from supermarket");
    await page.getByRole("button", { name: /^Create$/i }).click();

    // 5. Verify Todo appears in list
    await expect(page.getByText("Buy organic milk")).toBeVisible();
    await expect(page.getByText("Whole milk from supermarket")).toBeVisible();

    // 6. Toggle Todo completion
    const checkbox = page.locator('button[role="checkbox"]').first();
    await checkbox.click();

    // 7. Verify completed state (label has line-through)
    const label = page.getByText("Buy organic milk");
    await expect(label).toHaveClass(/line-through/);

    // 8. Logout
    await page.getByRole("button", { name: /Logout/i }).click();
    await expect(page).toHaveURL(/.*login/);
  });

  test("Scenario 2: Cross-User Data Isolation", async ({ page, browser }) => {
    const timestamp = Date.now();
    const emailA = `user_a_${timestamp}@example.com`;
    const emailB = `user_b_${timestamp}@example.com`;
    const password = "Password@123";

    // --- User A Session ---
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    await pageA.goto("/register");
    await pageA.fill("#email", emailA);
    await pageA.fill("#password", password);
    await pageA.fill("#confirmPassword", password);
    await pageA.click('button[type="submit"]');
    await expect(pageA).toHaveURL("/");

    // User A creates private todo
    const secretTitle = `User A Private Secret ${timestamp}`;
    await pageA.getByRole("button", { name: /Add Todo/i }).click();
    await pageA.fill("#title", secretTitle);
    await pageA.getByRole("button", { name: /^Create$/i }).click();
    await expect(pageA.getByText(secretTitle)).toBeVisible();

    // --- User B Session (Isolated Browser Context) ---
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    await pageB.goto("/register");
    await pageB.fill("#email", emailB);
    await pageB.fill("#password", password);
    await pageB.fill("#confirmPassword", password);
    await pageB.click('button[type="submit"]');
    await expect(pageB).toHaveURL("/");

    // User B must NOT see User A's todo
    await expect(pageB.getByText(secretTitle)).not.toBeVisible();
    await expect(pageB.getByText("No todos yet")).toBeVisible();

    await contextA.close();
    await contextB.close();
  });
});
