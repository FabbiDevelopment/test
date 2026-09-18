import { test, expect } from '@playwright/test';

test.describe('Todo User Journey', () => {
  const testEmail = `user_${Date.now()}@test.com`;
  const testPassword = 'password123';

  test('should register, login, create todo, toggle and logout', async ({ page }) => {
    // 1. Register
    await page.goto('/register');
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[name="password"]', testPassword);
    await page.fill('input[name="confirmPassword"]', testPassword);
    await page.click('button[type="submit"]');

    // Wait for redirect to dashboard
    await expect(page).toHaveURL('/');
    
    // 2. Create Todo
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[name="title"]', 'Playwright E2E Test');
    await page.fill('textarea[name="description"]', 'This is an automated test.');
    await page.click('button[type="submit"]');

    // Verify it appears in the list
    await expect(page.locator('label', { hasText: 'Playwright E2E Test' })).toBeVisible();

    // 3. Toggle Completion
    const checkbox = page.locator('button[role="checkbox"]').first();
    await checkbox.click();
    await expect(checkbox).toHaveAttribute('aria-checked', 'true');

    // Verify UI reflects checked state (line-through)
    const label = page.locator('label', { hasText: 'Playwright E2E Test' });
    await expect(label).toHaveClass(/line-through/);

    // 4. Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL('/login');
  });
});
