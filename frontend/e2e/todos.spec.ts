import { test, expect } from '@playwright/test';

const generateEmail = () => `test_${Math.random().toString(36).substring(7)}@example.com`;
const TEST_PASSWORD = 'password123';

test.describe('Todo Application E2E', () => {
  test('Full User Journey: Register -> Create -> Toggle -> Verify -> Logout', async ({ page }) => {
    const userEmail = generateEmail();

    // 1. Register & Login
    await page.goto('/');
    await page.getByRole('link', { name: 'Sign up' }).click();
    await page.getByLabel('Email').fill(userEmail);
    await page.getByLabel('Password', { exact: true }).fill(TEST_PASSWORD);
    await page.getByLabel('Confirm Password').fill(TEST_PASSWORD);
    await page.getByRole('button', { name: 'Create Account' }).click();

    // Should be automatically logged in and redirected to Todos
    await expect(page.getByText('My Todos').first()).toBeVisible();
    
    // 2. Create a todo
    await page.getByRole('button', { name: 'Add Todo' }).click();
    await page.getByLabel('Title').fill('My E2E Test Todo');
    await page.getByLabel('Description').fill('This is created by playwright');
    await page.getByRole('button', { name: 'Create' }).click();

    // 3. Verify item in UI
    const todoItem = page.locator('text=My E2E Test Todo');
    await expect(todoItem).toBeVisible();

    // 4. Toggle completion
    const checkbox = page.getByRole('checkbox').first();
    await checkbox.click(); // Radix UI Checkbox is a button
    await expect(checkbox).toBeChecked();

    // Untoggle
    await checkbox.click();
    await expect(checkbox).not.toBeChecked();

    // 5. Logout
    await page.getByRole('button', { name: 'Logout' }).click();
    await expect(page.getByRole('heading', { name: 'Welcome Back' })).toBeVisible();
  });

  test('Cross-User Data Isolation', async ({ browser }) => {
    const userA_Email = generateEmail();
    const userB_Email = generateEmail();

    // --- Context A (User A) ---
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    // Register User A
    await pageA.goto('/register');
    await pageA.getByLabel('Email').fill(userA_Email);
    await pageA.getByLabel('Password', { exact: true }).fill(TEST_PASSWORD);
    await pageA.getByLabel('Confirm Password').fill(TEST_PASSWORD);
    await pageA.getByRole('button', { name: 'Create Account' }).click();

    // User A is auto-logged in
    // Create private todo
    const uniqueTodoTitle = `Private Todo ${Math.random()}`;
    await pageA.getByRole('button', { name: 'Add Todo' }).click();
    await pageA.getByLabel('Title').fill(uniqueTodoTitle);
    await pageA.getByRole('button', { name: 'Create' }).click();
    await expect(pageA.locator(`text=${uniqueTodoTitle}`)).toBeVisible();
    await contextA.close();

    // --- Context B (User B) ---
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    // Register User B
    await pageB.goto('/register');
    await pageB.getByLabel('Email').fill(userB_Email);
    await pageB.getByLabel('Password', { exact: true }).fill(TEST_PASSWORD);
    await pageB.getByLabel('Confirm Password').fill(TEST_PASSWORD);
    await pageB.getByRole('button', { name: 'Create Account' }).click();

    // User B is auto-logged in
    // Verify User A's todo is NOT visible
    await expect(pageB.getByText('My Todos').first()).toBeVisible();
    await expect(pageB.locator(`text=${uniqueTodoTitle}`)).not.toBeVisible();
    await contextB.close();
  });
});
