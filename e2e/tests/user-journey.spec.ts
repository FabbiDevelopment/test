import { test, expect } from "@playwright/test";

test.describe("Scenario 1: Full User Journey", () => {
  test("Register -> Create Todo -> Toggle Completion -> Verify UI -> Logout", async ({
    page,
  }) => {
    const timestamp = Date.now();
    const email = `journey_${timestamp}@example.com`;
    const password = "Password@123";
    const todoTitle = `Automated Todo ${timestamp}`;
    const todoDesc = `Created by Playwright at ${new Date().toISOString()}`;

    // 1. Navigate to Register page
    await page.goto("/register");
    await expect(page).toHaveURL(/.*register/);

    // 2. Register a new user
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button[type="submit"]');

    // 3. Verify redirected to Dashboard
    await expect(page).toHaveURL("/", { timeout: 10000 });
    await expect(page.locator("text=My Todos")).toBeVisible();
    await expect(page.locator(`text=${email}`)).toBeVisible();

    // 4. Open Create Todo Dialog
    await page.click('button:has-text("Add Todo")');
    await expect(page.locator("text=Create Todo")).toBeVisible();

    // 5. Fill and submit Todo form
    await page.fill("#title", todoTitle);
    await page.fill("#description", todoDesc);
    await page.click('button[type="submit"]:has-text("Create")');

    // 6. Verify Todo appears in list
    const todoItem = page.locator(`text=${todoTitle}`);
    await expect(todoItem).toBeVisible();

    // 7. Toggle completion (Tick complete)
    const todoRow = page.locator("div.group", { hasText: todoTitle });
    const checkbox = todoRow.locator('button[role="checkbox"]');
    await checkbox.click();

    // Verify item has line-through style indicating completed
    const todoLabel = page.locator(`label:has-text("${todoTitle}")`);
    await expect(todoLabel).toHaveClass(/line-through/);

    // 8. Toggle back to incomplete (Untick)
    await checkbox.click();
    await expect(todoLabel).not.toHaveClass(/line-through/);

    // 9. Logout
    await page.click('button:has-text("Logout")');

    // 10. Verify redirected to Login page
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
    await expect(page.locator('button[type="submit"]:has-text("Sign In")')).toBeVisible();
  });
});
