import { test, expect } from '@playwright/test';

test.describe('Tier 2B: E2E Tests', () => {

  test('Full User Journey', async ({ page }) => {
    // 1. Register
    const testEmail = `user_${Date.now()}@test.com`;
    await page.goto('/register');
    await page.fill('input[type="email"]', testEmail);
    await page.fill('input[type="password"]', 'Test@1234');
    await page.fill('input[id="confirmPassword"]', 'Test@1234');
    await page.click('button[type="submit"]');

    // Should redirect to dashboard
    await expect(page).toHaveURL('/');
    await page.waitForLoadState('networkidle');

    // 2. Create a todo
    const todoTitle = `E2E Todo ${Date.now()}`;
    await page.getByRole('button', { name: 'Add Todo' }).click();
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.fill('input[placeholder="What needs to be done?"]', todoTitle);
    await page.fill('input[placeholder="Add details..."]', 'Playwright testing');

    // Wait for the POST response before checking the UI
    const [createResponse] = await Promise.all([
      page.waitForResponse(
        (res) => res.url().includes('/api/v1/todos') && res.request().method() === 'POST',
      ),
      page.getByRole('button', { name: 'Create' }).click(),
    ]);
    expect(createResponse.status()).toBe(201);

    // Wait for the list to refetch
    await page.waitForLoadState('networkidle');

    // 3. Verify item in UI
    await expect(page.getByText(todoTitle)).toBeVisible({ timeout: 10000 });

    // 4. Toggle completion — find the checkbox belonging to this item
    const parentDiv = page.locator('.flex.items-center.gap-3')
      .filter({ hasText: todoTitle })
      .first();
    const checkbox = parentDiv.locator('button[role="checkbox"]');
    await checkbox.click();
    await expect(checkbox).toHaveAttribute('aria-checked', 'true');

    // 5. Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    await expect(page).toHaveURL('/login');
  });

  test('Cross-User Data Isolation', async ({ browser }) => {
    // ---------- User A creates a private todo ----------
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();
    const emailA = `usera_${Date.now()}@test.com`;

    await pageA.goto('/register');
    await pageA.fill('input[type="email"]', emailA);
    await pageA.fill('input[type="password"]', 'Test@1234');
    await pageA.fill('input[id="confirmPassword"]', 'Test@1234');
    await pageA.click('button[type="submit"]');
    await expect(pageA).toHaveURL('/');
    await pageA.waitForLoadState('networkidle');

    const secretTodo = `Secret-${Date.now()}`;
    await pageA.getByRole('button', { name: 'Add Todo' }).click();
    await pageA.fill('input[placeholder="What needs to be done?"]', secretTodo);

    const [createResp] = await Promise.all([
      pageA.waitForResponse(
        (res) => res.url().includes('/api/v1/todos') && res.request().method() === 'POST',
      ),
      pageA.getByRole('button', { name: 'Create' }).click(),
    ]);
    expect(createResp.status()).toBe(201);

    await pageA.waitForLoadState('networkidle');
    await expect(pageA.getByText(secretTodo)).toBeVisible({ timeout: 10000 });

    // ---------- User B logs in and should NOT see User A's todo ----------
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();
    const emailB = `userb_${Date.now()}@test.com`;

    await pageB.goto('/register');
    await pageB.fill('input[type="email"]', emailB);
    await pageB.fill('input[type="password"]', 'Test@1234');
    await pageB.fill('input[id="confirmPassword"]', 'Test@1234');
    await pageB.click('button[type="submit"]');
    await expect(pageB).toHaveURL('/');
    await pageB.waitForLoadState('networkidle');

    // User B should NOT see User A's secret todo
    await expect(pageB.getByText(secretTodo)).toHaveCount(0);

    await contextA.close();
    await contextB.close();
  });
});
