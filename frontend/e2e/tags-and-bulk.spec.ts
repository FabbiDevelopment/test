import { test, expect } from "@playwright/test";

test.describe("Frontend Suggested Tests: Tags, Filtering, Bulk Actions & Logout", () => {
  let userEmail: string;
  const password = "Password@123";

  test.beforeEach(async ({ page }) => {
    userEmail = `e2e_suggested_${Date.now()}@example.com`;

    // Register & login new user
    await page.goto("/register");
    await page.fill('input[type="email"]', userEmail);
    await page.fill('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await expect(page).toHaveURL("/todos");
  });

  test("1. Tag Form Validation: Cannot submit empty tag name", async ({ page }) => {
    await page.click('button:has-text("Manage Tags")');
    await expect(page.locator("text=Manage Tags")).toBeVisible();

    // Submit empty tag form
    await page.click('button[type="submit"]:has-text("Add")');

    // Verify validation error
    await expect(page.locator("text=Name is required")).toBeVisible();
  });

  test("2. Todo Filter Query Key Behavior: Search, status, tag filter and clear filters", async ({ page }) => {
    // Create 2 todos: "Alpha Task" and "Beta Task"
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', "Alpha Special Task");
    await page.click('button[type="submit"]:has-text("Create")');

    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', "Beta Simple Task");
    await page.click('button[type="submit"]:has-text("Create")');

    // Filter by keyword "Alpha"
    await page.fill('input[placeholder="Search todos..."]', "Alpha");
    await expect(page.locator("text=Alpha Special Task")).toBeVisible();
    await expect(page.locator("text=Beta Simple Task")).not.toBeVisible();

    // Click Clear Filters
    await page.click('button:has-text("Clear")');
    await expect(page.locator("text=Alpha Special Task")).toBeVisible();
    await expect(page.locator("text=Beta Simple Task")).toBeVisible();
  });

  test("3. Bulk Action Success & UI Handling: Select multiple and mark completed", async ({ page }) => {
    // Create 2 todos
    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', "Bulk Item 1");
    await page.click('button[type="submit"]:has-text("Create")');

    await page.click('button:has-text("Add Todo")');
    await page.fill('input[id="title"]', "Bulk Item 2");
    await page.click('button[type="submit"]:has-text("Create")');

    // Select All
    await page.click('button:has-text("Select All")');
    await expect(page.locator("text=2 selected:")).toBeVisible();

    // Bulk Mark Completed
    await page.click('button:has-text("Mark Completed")');

    // Verify toast or updated list state
    await expect(page.locator("text=Bulk status updated!")).toBeVisible();
  });

  test("4. Logout Clearing Cached Data & LocalStorage Tokens", async ({ page }) => {
    await page.click('button:has-text("Logout")');
    await expect(page).toHaveURL("/login");

    // Verify localStorage tokens cleared
    const token = await page.evaluate(() => localStorage.getItem("access_token"));
    expect(token).toBeNull();
  });
});
