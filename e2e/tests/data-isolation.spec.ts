import { test, expect } from "@playwright/test";

test.describe("Scenario 2: Cross-User Data Isolation", () => {
  test("User A creates private todo; User B cannot see it in their session", async ({
    page,
  }) => {
    const timestamp = Date.now();
    const userAEmail = `user_a_${timestamp}@example.com`;
    const userBEmail = `user_b_${timestamp}@example.com`;
    const commonPassword = "Password@123";
    const privateTodoTitle = `CONFIDENTIAL_TODO_${timestamp}`;

    // --- STEP 1: User A registers and creates a private todo ---
    await page.goto("/register");
    await page.fill("#email", userAEmail);
    await page.fill("#password", commonPassword);
    await page.fill("#confirmPassword", commonPassword);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL("/", { timeout: 10000 });
    await expect(page.locator(`text=${userAEmail}`)).toBeVisible();

    // User A adds a secret todo
    await page.click('button:has-text("Add Todo")');
    await page.fill("#title", privateTodoTitle);
    await page.fill("#description", "Classified data for User A only");
    await page.click('button[type="submit"]:has-text("Create")');

    // Confirm User A sees their secret todo
    await expect(page.locator(`text=${privateTodoTitle}`)).toBeVisible();

    // --- STEP 2: User A logs out ---
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });

    // --- STEP 3: User B registers on a clean session ---
    await page.goto("/register");
    await page.fill("#email", userBEmail);
    await page.fill("#password", commonPassword);
    await page.fill("#confirmPassword", commonPassword);
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL("/", { timeout: 10000 });
    await expect(page.locator(`text=${userBEmail}`)).toBeVisible();

    // --- STEP 4: Confirm User B DOES NOT see User A's private todo ---
    const secretItemForUserB = page.locator(`text=${privateTodoTitle}`);
    await expect(secretItemForUserB).toHaveCount(0);

    // Confirm User B's list indicates no todos yet
    await expect(page.locator("text=No todos yet")).toBeVisible();
  });
});
