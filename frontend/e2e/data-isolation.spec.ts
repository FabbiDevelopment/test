import { test, expect } from "@playwright/test";

test.describe("Cross-User Data Isolation E2E Test", () => {
  test("User A creates private todo; User B logs in and confirms item is NOT visible", async ({ page }) => {
    const userAEmail = `user_a_${Date.now()}@example.com`;
    const userBEmail = `user_b_${Date.now()}@example.com`;
    const password = "Password@123";
    const privateTodoTitle = `User A Private Secret ${Date.now()}`;

    // 1. User A registers and logs in
    await page.goto("/register");
    await page.fill('input[type="email"]', userAEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/todos");

    // 2. User A creates a private todo
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', privateTodoTitle);
    await page.fill('input[id="description"]', "Confidential details");
    await page.click('button[type="submit"]:has-text("Create")');
    await expect(page.locator(`text=${privateTodoTitle}`)).toBeVisible();

    // 3. User A logs out
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL("/login");

    // 4. User B registers and logs in
    await page.goto("/register");
    await page.fill('input[type="email"]', userBEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/todos");

    // 5. User B confirms User A's private todo is NOT visible
    await expect(page.locator(`text=${privateTodoTitle}`)).not.toBeVisible();
    await expect(page.locator("text=No todos yet")).toBeVisible();
  });
});
