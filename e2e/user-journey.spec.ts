import { test, expect } from "@playwright/test";

test.describe("Full User Journey", () => {
  test("Register -> Create Todo -> Toggle Completion -> Verify UI -> Logout -> Login", async ({
    page,
  }) => {
    const timestamp = Date.now();
    const email = `testuser_${timestamp}@example.com`;
    const password = "Password123!";

    // 1. Navigate to Register page
    await page.goto("/register");
    await expect(page).toHaveURL("/register");

    // 2. Register a new user
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.fill("#confirmPassword", password);
    await page.click('button:has-text("Create Account")');

    // 3. Verify redirected to dashboard and user email is displayed
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page.getByText(email)).toBeVisible();

    // 4. Create a new todo
    await page.click('button:has-text("Add Todo")');
    await expect(page.getByRole("dialog")).toBeVisible();
    await page.fill("#title", `Task ${timestamp}`);
    await page.fill("#description", "Detailed task description");
    await page.click('button[type="submit"]');

    // 5. Verify todo item appears in list
    const todoItem = page.getByText(`Task ${timestamp}`);
    await expect(todoItem).toBeVisible({ timeout: 5000 });
    await expect(page.getByText("Detailed task description")).toBeVisible();

    // 6. Toggle completion
    const checkbox = page.locator('button[role="checkbox"]').first();
    await checkbox.click();
    await expect(checkbox).toHaveAttribute("data-state", "checked");

    // 7. Logout
    await page.click('button:has-text("Logout")');
    await page.waitForURL("/login", { timeout: 5000 });

    // 8. Log back in with the registered credentials
    await page.fill("#email", email);
    await page.fill("#password", password);
    await page.click('button:has-text("Sign In")');

    // 9. Verify dashboard and todo persistence
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page.getByText(email)).toBeVisible();
    await expect(page.getByText(`Task ${timestamp}`)).toBeVisible();
  });
});
