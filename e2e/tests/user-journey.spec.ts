import { test, expect } from "@playwright/test";

test.describe("Full User Journey E2E Test", () => {
  test("Register -> Create Todo -> Toggle Completion -> Verify UI -> Logout", async ({ page }) => {
    const timestamp = Date.now();
    const userEmail = `journey_${timestamp}@test.com`;
    const password = "Password@123";
    const todoTitle = `E2E Task ${timestamp}`;
    const todoDesc = "Automated test description";

    // 1. Navigate to Register page
    await page.goto("/register");
    await expect(page).toHaveURL(/.*register/);

    // 2. Register account
    await page.fill('input[id="email"]', userEmail);
    await page.fill('input[id="password"]', password);
    await page.fill('input[id="confirmPassword"]', password);
    await page.click('button[type="submit"]');

    // 3. Verify redirected to main dashboard
    await expect(page).toHaveURL(/.*(\/|$)/);
    await expect(page.locator("text=Todo App")).toBeVisible();
    await expect(page.locator(`text=${userEmail}`)).toBeVisible();

    // 4. Create a Todo
    await page.click('button:has-text("Add Todo")');
    await expect(page.locator('text="Create Todo"')).toBeVisible();

    await page.fill('input[id="title"]', todoTitle);
    await page.fill('input[id="description"]', todoDesc);
    await page.click('button[type="submit"]:has-text("Create")');

    // 5. Verify Todo appears in list
    await expect(page.locator(`text=${todoTitle}`)).toBeVisible();
    await expect(page.locator(`text=${todoDesc}`)).toBeVisible();

    // 6. Toggle Completion
    await page.locator(`label:has-text("${todoTitle}")`).click();

    // Verify strike-through / completed state
    const todoLabel = page.locator(`label:has-text("${todoTitle}")`);
    await expect(todoLabel).toHaveClass(/line-through/);

    // 7. Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*login/);

    // Verify tokens removed from localStorage
    const accessToken = await page.evaluate(() => localStorage.getItem("access_token"));
    expect(accessToken).toBeNull();
  });
});
