import { test, expect } from "@playwright/test";

/**
 * E2E Scenario 1 — Full user journey (Hành trình người dùng đầy đủ)
 * Register → Create todo → Toggle completed → Verify UI → Logout
 */
test.describe("Full user journey", () => {
  const uniqueEmail = `e2e-journey-${Date.now()}@test.com`;
  const password = "password123";
  const todoTitle = `E2E Todo ${Date.now()}`;

  test("register, create todo, toggle completed, verify UI, logout", async ({
    page,
  }) => {
    // Step 1: Register — Đăng ký tài khoản mới
    await page.goto("/register");
    await page.getByLabel("Email").fill(uniqueEmail);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByLabel("Confirm Password").fill(password);
    await page.getByRole("button", { name: "Create Account" }).click();

    // Step 2: Verify redirect to dashboard — Xác minh chuyển hướng
    await expect(page.getByText("My Todos")).toBeVisible({ timeout: 10_000 });
    await expect(page.getByText(uniqueEmail)).toBeVisible();

    // Step 3: Create todo — Tạo việc cần làm
    await page.getByRole("button", { name: "Add Todo" }).click();
    await page.getByLabel("Title").fill(todoTitle);
    await page.getByRole("button", { name: "Create" }).click();
    await expect(page.getByText(todoTitle)).toBeVisible();

    // Step 4: Toggle completed ON — Bật trạng thái hoàn thành
    const checkbox = page.getByRole("checkbox", { name: todoTitle });
    await checkbox.click();
    await expect(page.locator(`label:has-text("${todoTitle}")`)).toHaveClass(
      /line-through/
    );

    // Step 5: Toggle completed OFF — Tắt trạng thái hoàn thành
    await checkbox.click();
    await expect(page.locator(`label:has-text("${todoTitle}")`)).not.toHaveClass(
      /line-through/
    );

    // Step 6: Logout — Đăng xuất
    await page.getByRole("button", { name: "Logout" }).click();
    await expect(page.getByRole("button", { name: "Sign In" })).toBeVisible({
      timeout: 10_000,
    });
  });
});
