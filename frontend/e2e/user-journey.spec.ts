import { test, expect } from "@playwright/test";

test.describe("Full User Journey E2E Test", () => {
  test("Register/Login -> Create Todo -> Toggle Completion -> Verify -> Logout", async ({ page }) => {
    const uniqueEmail = `e2e_journey_${Date.now()}@example.com`;
    const password = "Password@123";

    // 1. Register new user
    await page.goto("/register");
    await page.fill('input[type="email"]', uniqueEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');

    // 2. Redirected to Todo page
    await expect(page).toHaveURL("/todos");
    await expect(page.locator("h1")).toContainText("Todo App");
    await expect(page.locator("p")).toContainText(uniqueEmail);

    // 3. Create a new Todo
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', "E2E Full Journey Todo");
    await page.fill('input[id="description"]', "Description for E2E test");
    await page.click('button[type="submit"]:has-text("Create")');

    // Verify item created
    await expect(page.locator("text=E2E Full Journey Todo")).toBeVisible();
    await expect(page.locator("text=Description for E2E test")).toBeVisible();

    // 4. Toggle completion
    const checkbox = page.locator('input[type="checkbox"]').first();
    await checkbox.check();

    // 5. Verify item marked completed (line-through class or checked state)
    await expect(checkbox).toBeChecked();

    // 6. Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL("/login");
  });
});
