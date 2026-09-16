import { test, expect } from '@playwright/test';

test.describe('E2E Full User Journey', () => {
  const timestamp = Date.now();
  const testUser = {
    email: `journey_user_${timestamp}@example.com`,
    password: 'Password123!',
  };
  const todoTitle = `E2E Task ${timestamp}`;
  const todoDescription = 'This task was created during Playwright automated user journey';

  test('completes full journey: Register -> Login -> Create Todo -> Toggle Complete -> Logout', async ({ page }) => {
    // ----------------------------------------------------
    // Step 1: User Registration
    // ----------------------------------------------------
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /create account/i })).toBeVisible();

    await page.fill('#email', testUser.email);
    await page.fill('#password', testUser.password);
    await page.fill('#confirmPassword', testUser.password);
    await page.click('button[type="submit"]');

    // Wait for navigation to dashboard (auto-logged in upon registration)
    await expect(page).toHaveURL('/');
    await expect(page.getByRole('heading', { name: 'Todo App' })).toBeVisible();

    // ----------------------------------------------------
    // Step 2: Logout and Re-Login to verify both auth flows
    // ----------------------------------------------------
    await page.getByRole('button', { name: /logout/i }).click();
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('heading', { name: /welcome back/i })).toBeVisible();

    // Sign in with the newly registered user
    await page.fill('#email', testUser.email);
    await page.fill('#password', testUser.password);
    await page.getByRole('button', { name: /sign in/i }).click();

    // Verify successful login landed on dashboard
    await expect(page).toHaveURL('/');
    await expect(page.getByText(testUser.email)).toBeVisible();

    // ----------------------------------------------------
    // Step 3: Create a new Todo item
    // ----------------------------------------------------
    await page.getByRole('button', { name: /add todo/i }).click();

    // Fill Create Todo dialog form
    await expect(page.getByRole('heading', { name: /create todo/i })).toBeVisible();
    await page.fill('#title', todoTitle);
    await page.fill('#description', todoDescription);
    await page.getByRole('button', { name: /^create$/i }).click();

    // Confirm todo item appears in the list
    const todoLabel = page.locator(`label:has-text("${todoTitle}")`);
    await expect(todoLabel).toBeVisible({ timeout: 10000 });
    await expect(page.getByText(todoDescription)).toBeVisible();

    // ----------------------------------------------------
    // Step 4: Toggle Complete and verify state persistence
    // ----------------------------------------------------
    // The todo label initially does not have line-through
    await expect(todoLabel).not.toHaveClass(/line-through/);

    // Click checkbox to complete todo
    const todoRow = page.locator('div.group', { has: page.getByText(todoTitle) });
    const checkbox = todoRow.getByRole('checkbox');
    await checkbox.click();

    // Verify title now has line-through styling
    await expect(todoLabel).toHaveClass(/line-through/);

    // Refresh page to guarantee status was persisted in backend DB
    await page.reload();
    const reloadedLabel = page.locator(`label:has-text("${todoTitle}")`);
    await expect(reloadedLabel).toBeVisible();
    await expect(reloadedLabel).toHaveClass(/line-through/);

    // ----------------------------------------------------
    // Step 5: Logout
    // ----------------------------------------------------
    await page.getByRole('button', { name: /logout/i }).click();
    await expect(page).toHaveURL(/\/login/);

    // Verify navigating back to / redirects to /login (protected route)
    await page.goto('/');
    await expect(page).toHaveURL(/\/login/);
  });
});
