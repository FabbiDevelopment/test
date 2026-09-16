import { test, expect } from '@playwright/test';

test.describe('E2E Cross-User Data Isolation', () => {
  const timestamp = Date.now();
  const userA = {
    email: `isolation_a_${timestamp}@example.com`,
    password: 'Password123!',
    todoTitle: `Confidential Todo User A [${timestamp}]`,
  };

  const userB = {
    email: `isolation_b_${timestamp}@example.com`,
    password: 'Password123!',
    todoTitle: `Private Todo User B [${timestamp}]`,
  };

  test('ensures complete data isolation: User A todos are never visible to User B', async ({ browser }) => {
    // ----------------------------------------------------
    // Context A: User A registers and creates a confidential todo
    // ----------------------------------------------------
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    await pageA.goto('/register');
    await pageA.fill('#email', userA.email);
    await pageA.fill('#password', userA.password);
    await pageA.fill('#confirmPassword', userA.password);
    await pageA.click('button[type="submit"]');

    await expect(pageA).toHaveURL('/');
    await expect(pageA.getByText(userA.email)).toBeVisible();

    // User A adds confidential todo
    await pageA.getByRole('button', { name: /add todo/i }).click();
    await pageA.fill('#title', userA.todoTitle);
    await pageA.fill('#description', 'Top secret notes belonging only to User A');
    await pageA.getByRole('button', { name: /^create$/i }).click();

    // Confirm todo is visible for User A
    await expect(pageA.getByText(userA.todoTitle)).toBeVisible();

    // ----------------------------------------------------
    // Context B: User B registers in an isolated browser session
    // ----------------------------------------------------
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    await pageB.goto('/register');
    await pageB.fill('#email', userB.email);
    await pageB.fill('#password', userB.password);
    await pageB.fill('#confirmPassword', userB.password);
    await pageB.click('button[type="submit"]');

    await expect(pageB).toHaveURL('/');
    await expect(pageB.getByText(userB.email)).toBeVisible();

    // CRITICAL ASSERTION: User B must NEVER see User A's confidential todo
    await expect(pageB.getByText(userA.todoTitle)).not.toBeVisible();

    // User B adds their own todo
    await pageB.getByRole('button', { name: /add todo/i }).click();
    await pageB.fill('#title', userB.todoTitle);
    await pageB.fill('#description', 'User B independent tasks');
    await pageB.getByRole('button', { name: /^create$/i }).click();

    // User B sees their own todo
    await expect(pageB.getByText(userB.todoTitle)).toBeVisible();

    // User B still cannot see User A's todo
    await expect(pageB.getByText(userA.todoTitle)).not.toBeVisible();

    // ----------------------------------------------------
    // Verify Context A remains isolated from User B's todos
    // ----------------------------------------------------
    await pageA.reload();
    await expect(pageA.getByText(userA.todoTitle)).toBeVisible();
    await expect(pageA.getByText(userB.todoTitle)).not.toBeVisible();

    // Clean up contexts
    await contextA.close();
    await contextB.close();
  });
});
