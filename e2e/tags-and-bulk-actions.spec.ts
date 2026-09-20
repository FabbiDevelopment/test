import { test, expect } from "@playwright/test";

test.describe("Tier 4: Tags, Filtering & Bulk Actions", () => {
  const timestamp = Date.now();
  const user = {
    email: `tier4_user_${timestamp}@example.com`,
    password: "Password123!",
  };

  test("Create Tag -> Attach Tag -> Filter by Keyword -> Bulk Complete", async ({
    page,
  }) => {
    // 1. Register & Login
    await page.goto("/register");
    await page.fill("#email", user.email);
    await page.fill("#password", user.password);
    await page.fill("#confirmPassword", user.password);
    await page.click('button:has-text("Create Account")');

    // Wait for redirect to /
    await page.waitForURL("/", { timeout: 10000 });
    await expect(page.getByText(user.email)).toBeVisible();

    // 2. Open Tag Manager & Create a Tag
    await page.click('button:has-text("Tags")');
    const tagDialog = page.getByRole("dialog");
    await expect(tagDialog).toBeVisible();
    await tagDialog.locator("#tag-name").fill("UrgentWork");
    await tagDialog.locator('button[type="submit"]').click();
    await expect(tagDialog.getByText("UrgentWork")).toBeVisible();

    // Close Tag Manager Dialog (by pressing Escape)
    await page.keyboard.press("Escape");
    await expect(tagDialog).not.toBeVisible();

    // 3. Create 2 Todos
    // Todo 1
    await page.click('button:has-text("Add Todo")');
    const todoDialog1 = page.getByRole("dialog");
    await expect(todoDialog1).toBeVisible();
    await todoDialog1.locator("#title").fill("Prepare Quarterly Report");
    await todoDialog1.locator("#description").fill("Financial breakdown for Q3");
    await todoDialog1.locator('button[type="submit"]').click();
    await expect(page.locator("text=Prepare Quarterly Report")).toBeVisible();

    // Todo 2
    await page.click('button:has-text("Add Todo")');
    const todoDialog2 = page.getByRole("dialog");
    await expect(todoDialog2).toBeVisible();
    await todoDialog2.locator("#title").fill("Buy office supplies");
    await todoDialog2.locator("#description").fill("Stationery and coffee beans");
    await todoDialog2.locator('button[type="submit"]').click();
    await expect(page.locator("text=Buy office supplies")).toBeVisible();

    // 4. Attach Tag to Todo 1
    const todoItem1 = page.locator("div.group", {
      hasText: "Prepare Quarterly Report",
    });
    await todoItem1.locator('button:has-text("Tag")').click();
    await page.click('button:has-text("UrgentWork")');
    await expect(todoItem1.locator("text=UrgentWork")).toBeVisible();

    // 5. Test Keyword Search Filtering
    await page.fill('input[placeholder*="Search todos"]', "Quarterly");
    await page.waitForTimeout(500);
    await expect(page.locator("text=Prepare Quarterly Report")).toBeVisible();
    await expect(page.locator("text=Buy office supplies")).not.toBeVisible();

    // Clear filter
    await page.click('button:has-text("Clear")');
    await page.waitForTimeout(500);
    await expect(page.locator("text=Prepare Quarterly Report")).toBeVisible();
    await expect(page.locator("text=Buy office supplies")).toBeVisible();

    // 6. Test Bulk Actions (Select All -> Mark Completed)
    await page.click("#select-all-todos");
    await expect(page.locator("text=2 todos selected")).toBeVisible();

    // Click "Mark Completed"
    await page.click('button:has-text("Mark Completed")');
    await page.waitForTimeout(500);

    // Verify both todos have completed styling (line-through)
    const label1 = page.locator('label:has-text("Prepare Quarterly Report")');
    const label2 = page.locator('label:has-text("Buy office supplies")');
    await expect(label1).toHaveClass(/line-through/);
    await expect(label2).toHaveClass(/line-through/);

    // 7. Test Bulk Delete (Select All -> Click Delete -> Accept Dialog)
    await page.click("#select-all-todos");
    await expect(page.locator("text=2 todos selected")).toBeVisible();

    page.once("dialog", (dialog) => dialog.accept());
    await page.click('button:has-text("Delete")');
    await page.waitForTimeout(500);

    // Verify todos are removed and empty state is shown
    await expect(page.locator("text=Prepare Quarterly Report")).not.toBeVisible();
    await expect(page.locator("text=Buy office supplies")).not.toBeVisible();
    await expect(page.locator("text=No todos found")).toBeVisible();
  });
});

