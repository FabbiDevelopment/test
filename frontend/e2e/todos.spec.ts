import { test, expect } from '@playwright/test';

test.describe('Todo Application E2E Tests', () => {

  test('Scenario 1: Full User Journey (Register -> Create Todo -> Toggle -> Verify -> Logout)', async ({ page }) => {
    const timestamp = Date.now();
    const email = `e2e_user_${timestamp}@example.com`;
    const password = 'Password@123';
    const todoTitle = `Automated Todo Task ${timestamp}`;
    const todoDescription = 'This is an end-to-end automated test task.';

    // 1. Navigate to register page
    await page.goto('/register');
    await expect(page).toHaveURL(/.*register/);

    // 2. Fill registration form
    await page.fill('input#email', email);
    await page.fill('input#password', password);
    await page.fill('input#confirmPassword', password);
    await page.click('button[type="submit"]');

    // 3. Verify redirected to dashboard & authenticated
    await expect(page).toHaveURL('/', { timeout: 10000 });
    await expect(page.getByText('My Todos')).toBeVisible();
    await expect(page.getByText(email)).toBeVisible();

    // 4. Open create todo modal
    await page.click('button:has-text("Add Todo")');
    await expect(page.getByRole('heading', { name: 'Create Todo' })).toBeVisible();

    // 5. Fill and submit todo form
    await page.fill('input#title', todoTitle);
    await page.fill('input#description', todoDescription);
    await page.click('button[type="submit"]:has-text("Create")');

    // 6. Verify todo item is displayed in the list
    const todoItem = page.getByText(todoTitle);
    await expect(todoItem).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(todoDescription)).toBeVisible();

    // 7. Toggle completion
    const checkbox = page.locator('button[role="checkbox"]').first();
    await checkbox.click();

    // 8. Verify completed status (checkbox checked and title line-through)
    await expect(checkbox).toHaveAttribute('data-state', 'checked');
    await expect(todoItem).toHaveClass(/line-through/);

    // 9. Logout
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });
  });

  test('Scenario 2: Cross-User Data Isolation', async ({ page }) => {
    const timestamp = Date.now();
    const userAEmail = `user_a_${timestamp}@example.com`;
    const userBEmail = `user_b_${timestamp}@example.com`;
    const password = 'Password@123';
    const privateTodoTitle = `User A Confidential Plan ${timestamp}`;

    // 1. Register User A
    await page.goto('/register');
    await page.fill('input#email', userAEmail);
    await page.fill('input#password', password);
    await page.fill('input#confirmPassword', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/', { timeout: 10000 });

    // 2. User A creates a private todo
    await page.click('button:has-text("Add Todo")');
    await page.fill('input#title', privateTodoTitle);
    await page.click('button[type="submit"]:has-text("Create")');
    await expect(page.getByText(privateTodoTitle)).toBeVisible({ timeout: 5000 });

    // 3. User A logs out
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL(/.*login/, { timeout: 10000 });

    // 4. Register and login User B
    await page.goto('/register');
    await page.fill('input#email', userBEmail);
    await page.fill('input#password', password);
    await page.fill('input#confirmPassword', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL('/', { timeout: 10000 });

    // 5. Verify User B does NOT see User A's private todo
    await expect(page.getByText(privateTodoTitle)).not.toBeVisible();

    // 6. User B creates their own todo
    const userBTodoTitle = `User B Independent Todo ${timestamp}`;
    await page.click('button:has-text("Add Todo")');
    await page.fill('input#title', userBTodoTitle);
    await page.click('button[type="submit"]:has-text("Create")');

    // 7. Verify only User B's todo is visible
    await expect(page.getByText(userBTodoTitle)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(privateTodoTitle)).not.toBeVisible();
  });

});
