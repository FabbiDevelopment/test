import { test, expect } from "@playwright/test";

test.describe("Cross-User Data Isolation", () => {
  test("User A creates private todo; User B cannot see it", async ({ page }) => {
    const timestamp = Date.now();
    const userAEmail = `user_a_${timestamp}@example.com`;
    const userBEmail = `user_b_${timestamp}@example.com`;
    const password = "Password123!";
    const secretTitle = `User A Secret Task ${timestamp}`;

    // 1. User A registers and creates a private todo
    await page.goto("/register");
    await page.fill("#email", userAEmail);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button:has-text("Create Account")');
    await page.waitForURL("/", { timeout: 10000 });

    await page.click('button:has-text("Add Todo")');
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.fill("#title", secretTitle);
    await page.click('button[type="submit"]');
    await expect(page.getByText(secretTitle)).toBeVisible({ timeout: 5000 });

    // 2. User A logs out
    await page.click('button:has-text("Logout")');
    await page.waitForURL("/login", { timeout: 5000 });

    // 3. User B registers
    await page.goto("/register");
    await page.fill("#email", userBEmail);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button:has-text("Create Account")');
    await page.waitForURL("/", { timeout: 10000 });

    // 4. Verify User A's secret task is NOT visible to User B
    await expect(page.getByText(secretTitle)).not.toBeVisible();

    // 5. User B creates their own todo
    const userBTask = `User B Task ${timestamp}`;
    await page.click('button:has-text("Add Todo")');
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.fill("#title", userBTask);
    await page.click('button[type="submit"]');

    // 6. User B sees their own task, but still not User A's task
    await expect(page.getByText(userBTask)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(secretTitle)).not.toBeVisible();
  });
});
