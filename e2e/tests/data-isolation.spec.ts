import { test, expect } from "@playwright/test";

test.describe("Cross-User Data Isolation E2E Test", () => {
  test("User A creates private todo; User B cannot see it", async ({ page }) => {
    const timestamp = Date.now();
    const userA = `user_a_${timestamp}@test.com`;
    const userB = `user_b_${timestamp}@test.com`;
    const password = "Password@123";
    const privateTitle = `Secret Todo Alpha ${timestamp}`;

    // Step 1: User A registers and creates a private todo
    await page.goto("/register");
    await page.fill('input[id="email"]', userA);
    await page.fill('input[id="password"]', password);
    await page.fill('input[id="confirmPassword"]', password);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*(\/|$)/);
    await expect(page.locator(`text=${userA}`)).toBeVisible();

    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', privateTitle);
    await page.click('button[type="submit"]:has-text("Create")');

    // Confirm visible for User A
    await expect(page.locator(`text=${privateTitle}`)).toBeVisible();

    // Step 2: User A logs out
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*login/);

    // Step 3: User B registers and logs in
    await page.goto("/register");
    await page.fill('input[id="email"]', userB);
    await page.fill('input[id="password"]', password);
    await page.fill('input[id="confirmPassword"]', password);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL(/.*(\/|$)/);
    await expect(page.locator(`text=${userB}`)).toBeVisible();

    // Step 4: Verify User A's private todo is NOT visible for User B
    await expect(page.locator(`text=${privateTitle}`)).toHaveCount(0);
    await expect(page.locator("text=No todos yet")).toBeVisible();
  });
});
