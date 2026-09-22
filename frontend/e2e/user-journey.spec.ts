import { test, expect } from '@playwright/test';

test.describe('Scenario 1: Full User Journey', () => {
  const timestamp = Date.now();
  const testEmail = `user_journey_${timestamp}@test.com`;
  const testPassword = 'Password@123';
  const todoTitle = `Todo Item ${timestamp}`;
  const todoDesc = `Detailed description for ${timestamp}`;

  test('Register -> Create Todo -> Toggle Completion -> Verify UI -> Logout', async ({ page }) => {
    // 1. Navigate to Register page
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /create an account/i })).toBeVisible();

    // 2. Fill registration form
    await page.locator('#email').fill(testEmail);
    await page.locator('#password').fill(testPassword);
    await page.locator('#confirmPassword').fill(testPassword);
    await page.getByRole('button', { name: /create account/i }).click();

    // 3. Verify redirected to Todo page & authenticated
    await expect(page).toHaveURL('/');
    await expect(page.getByText(testEmail)).toBeVisible();
    await expect(page.getByRole('heading', { name: /my todos/i })).toBeVisible();

    // 4. Create a new Todo
    await page.getByRole('button', { name: /add todo/i }).click();
    await expect(page.getByRole('heading', { name: /create todo/i })).toBeVisible();

    await page.locator('#title').fill(todoTitle);
    await page.locator('#description').fill(todoDesc);
    await page.getByRole('button', { name: /create/i }).click();

    // 5. Verify todo appears in list
    const todoItem = page.locator('div.group', { hasText: todoTitle });
    await expect(todoItem).toBeVisible();
    await expect(todoItem.getByText(todoDesc)).toBeVisible();

    // 6. Toggle completion
    const checkbox = todoItem.getByRole('checkbox');
    await expect(checkbox).not.toBeChecked();
    await checkbox.click();

    // Verify item in UI is marked completed (checked + line-through)
    await expect(checkbox).toBeChecked();
    const titleLabel = todoItem.locator('label', { hasText: todoTitle });
    await expect(titleLabel).toHaveClass(/line-through/);

    // 7. Logout
    await page.getByRole('button', { name: /logout/i }).click();

    // Verify redirected to Login page
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });
});
