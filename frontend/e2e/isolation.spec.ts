import { test, expect } from '@playwright/test';

test.describe('Cross-User Data Isolation', () => {
  const userA = `usera_${Date.now()}@test.com`;
  const userB = `userb_${Date.now()}@test.com`;
  const password = 'password123';

  test('User B should not see User A\'s todos', async ({ page, browser }) => {
    // Setup User A
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    
    await pageA.goto('/register');
    await pageA.fill('input[type="email"]', userA);
    await pageA.fill('input[name="password"]', password);
    await pageA.fill('input[name="confirmPassword"]', password);
    await pageA.click('button[type="submit"]');
    await expect(pageA).toHaveURL('/');

    // User A creates a secret todo
    await pageA.click('button:has-text("Add Todo")');
    await pageA.fill('input[name="title"]', 'Top Secret Todo A');
    await pageA.click('button[type="submit"]');
    await expect(pageA.locator('label', { hasText: 'Top Secret Todo A' })).toBeVisible();
    await contextA.close(); // User A leaves

    // Setup User B
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    
    await pageB.goto('/register');
    await pageB.fill('input[type="email"]', userB);
    await pageB.fill('input[name="password"]', password);
    await pageB.fill('input[name="confirmPassword"]', password);
    await pageB.click('button[type="submit"]');
    await expect(pageB).toHaveURL('/');

    // User B should NOT see User A's todo
    await expect(pageB.locator('label', { hasText: 'Top Secret Todo A' })).toHaveCount(0);
    
    // Clean up
    await contextB.close();
  });
});
