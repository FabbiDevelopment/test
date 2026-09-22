import { test, expect } from '@playwright/test';

test.describe('Scenario 2: Cross-User Data Isolation', () => {
  const timestamp = Date.now();
  const userAEmail = `user_a_${timestamp}@test.com`;
  const userBEmail = `user_b_${timestamp}@test.com`;
  const password = 'Password@123';
  const privateTodoTitle = `Private Confidential Todo ${timestamp}`;

  test('User A creates private todo, User B in another session confirms item is NOT visible', async ({ browser }) => {
    // Session A: User A
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    // 1. User A registers and logs in
    await pageA.goto('/register');
    await pageA.locator('#email').fill(userAEmail);
    await pageA.locator('#password').fill(password);
    await pageA.locator('#confirmPassword').fill(password);
    await pageA.getByRole('button', { name: /create account/i }).click();

    await expect(pageA).toHaveURL('/');
    await expect(pageA.getByText(userAEmail)).toBeVisible();

    // 2. User A creates a private Todo
    await pageA.getByRole('button', { name: /add todo/i }).click();
    await pageA.locator('#title').fill(privateTodoTitle);
    await pageA.locator('#description').fill('Confidential to User A only');
    await pageA.getByRole('button', { name: /create/i }).click();

    // Verify User A can see their own todo
    await expect(pageA.getByText(privateTodoTitle)).toBeVisible();

    // Session B: User B in an isolated browser context
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    // 3. User B registers and logs in
    await pageB.goto('/register');
    await pageB.locator('#email').fill(userBEmail);
    await pageB.locator('#password').fill(password);
    await pageB.locator('#confirmPassword').fill(password);
    await pageB.getByRole('button', { name: /create account/i }).click();

    await expect(pageB).toHaveURL('/');
    await expect(pageB.getByText(userBEmail)).toBeVisible();

    // 4. Verify User B CANNOT see User A's private todo
    await expect(pageB.getByText(privateTodoTitle)).not.toBeVisible();
    await expect(pageB.getByText(/no todos yet/i)).toBeVisible();

    // Cleanup contexts
    await contextA.close();
    await contextB.close();
  });
});
