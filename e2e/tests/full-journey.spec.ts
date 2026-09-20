import { test, expect } from "@playwright/test";

/**
 * Scenario 1: Full User Journey
 *
 * Steps:
 * 1. Register with a new unique email
 * 2. Redirected to dashboard (authenticated)
 * 3. Create a new todo
 * 4. Verify todo appears in the list
 * 5. Toggle todo to completed (checkbox → checked, title strikethrough)
 * 6. Toggle back to incomplete (checkbox → unchecked)
 * 7. Logout → redirected to /login
 */

const uniqueEmail = () => `e2e_journey_${Date.now()}@test.com`;

test.describe("Full User Journey", () => {
  test("register → create todo → toggle completion → logout", async ({ page }) => {
    const email = uniqueEmail();
    const password = "Password@123";
    const todoTitle = `E2E Test Todo ${Date.now()}`;

    // ── Step 1: Register ───────────────────────────────────────────────────
    await page.goto("/register");
    await expect(page).toHaveURL(/register/);

    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /register|sign up|create account/i }).click();

    // ── Step 2: Redirected to dashboard ───────────────────────────────────
    await expect(page).toHaveURL("/", { timeout: 10_000 });
    await expect(page.getByText("My Todos")).toBeVisible();

    // ── Step 3: Create a todo ──────────────────────────────────────────────
    await page.getByRole("button", { name: /add todo/i }).click();

    // Fill in the todo form (modal/dialog)
    await page.getByLabel(/title/i).fill(todoTitle);
    await page.getByRole("button", { name: /save|create|submit|add/i }).click();

    // ── Step 4: Verify todo appears in list ───────────────────────────────
    await expect(page.getByText(todoTitle)).toBeVisible({ timeout: 8_000 });

    // ── Step 5: Toggle to completed ───────────────────────────────────────
    const todoItem = page.locator(`label:has-text("${todoTitle}")`);
    const checkbox = page.locator(`#todo-${await page.locator(`[id^="todo-"]`).first().getAttribute("id")?.then(id => id)}`).first();

    // Use the checkbox associated with our todo title
    const todoRow = page.locator(`div:has(label:has-text("${todoTitle}"))`).first();
    const todoCheckbox = todoRow.locator('input[type="checkbox"], [role="checkbox"]').first();

    await todoCheckbox.click();

    // Title should now have line-through style (completed)
    await expect(todoItem).toHaveClass(/line-through/, { timeout: 5_000 });

    // ── Step 6: Toggle back to incomplete ────────────────────────────────
    await todoCheckbox.click();

    // Title should no longer have line-through (incomplete)
    await expect(todoItem).not.toHaveClass(/line-through/, { timeout: 5_000 });

    // ── Step 7: Logout ────────────────────────────────────────────────────
    await page.getByRole("button", { name: /logout/i }).click();

    await expect(page).toHaveURL(/login/, { timeout: 8_000 });
    await expect(page.getByLabel(/email/i)).toBeVisible();
  });

  test("login flow after registration", async ({ page }) => {
    const email = uniqueEmail();
    const password = "Password@123";

    // Register first
    await page.goto("/register");
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /register|sign up|create account/i }).click();
    await expect(page).toHaveURL("/", { timeout: 10_000 });

    // Logout
    await page.getByRole("button", { name: /logout/i }).click();
    await expect(page).toHaveURL(/login/, { timeout: 8_000 });

    // Login again
    await page.getByLabel(/email/i).fill(email);
    await page.getByLabel(/password/i).fill(password);
    await page.getByRole("button", { name: /login|sign in/i }).click();

    // Should be back on dashboard
    await expect(page).toHaveURL("/", { timeout: 10_000 });
    await expect(page.getByText("My Todos")).toBeVisible();
  });
});
