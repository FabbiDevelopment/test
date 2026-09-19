import { test, expect, Browser } from "@playwright/test";

// ─── Helpers ────────────────────────────────────────────────────────────────

/** Sinh email ngẫu nhiên để tránh trùng khi chạy lại */
function randomEmail(prefix = "e2e") {
  return `${prefix}-${Date.now()}-${Math.floor(Math.random() * 9999)}@example.com`;
}

/** Đăng ký user mới và đợi redirect về "/" */
async function registerUser(
  page: import("@playwright/test").Page,
  email: string,
  password = "Test@1234"
) {
  await page.goto("/register");
  await page.locator("#email").fill(email);
  await page.locator("#password").fill(password);
  await page.locator("#confirmPassword").fill(password);
  await page.getByRole("button", { name: "Create Account" }).click();
  await expect(page).toHaveURL("/");
}

// ─── Test 1: Complete user flow ──────────────────────────────────────────────

test("complete user flow: register, create todo, toggle, delete", async ({
  page,
}) => {
  const email = randomEmail("flow");

  // 1. Đăng ký và assert redirect về Dashboard
  await registerUser(page, email);

  // 2. Tạo todo mới qua dialog "Add Todo"
  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.locator("#title").fill("E2E Test Todo");
  // description là optional — bỏ qua nếu dialog không yêu cầu
  const descInput = page.locator("#description");
  if (await descInput.isVisible()) {
    await descInput.fill("Created by Playwright");
  }
  await page.getByRole("button", { name: "Create" }).click();

  // 3. Assert todo xuất hiện trong danh sách
  await expect(page.getByText("E2E Test Todo")).toBeVisible();

  // 4. Toggle checkbox (completed)
  const todoItem = page.locator("div", { hasText: "E2E Test Todo" }).first();
  const checkbox = todoItem.locator('input[type="checkbox"]');
  await checkbox.click();
  await expect(checkbox).toBeChecked();

  // 5. Xóa todo — tìm button xóa (Trash2) trong cùng div chứa text todo
  const deleteButton = todoItem.locator("button").last();
  await deleteButton.click();

  // 6. Assert todo đã biến mất khỏi trang
  await expect(page.getByText("E2E Test Todo")).not.toBeVisible();
});

// ─── Test 2: Cross-user data isolation ──────────────────────────────────────

test("cross-user data isolation: user B does not see user A todos", async ({
  browser,
}: {
  browser: Browser;
}) => {
  // Tạo 2 context hoàn toàn độc lập (mỗi context = 1 trình duyệt riêng biệt)
  const contextA = await browser.newContext();
  const contextB = await browser.newContext();

  const pageA = await contextA.newPage();
  const pageB = await contextB.newPage();

  try {
    const emailA = randomEmail("user-a");
    const emailB = randomEmail("user-b");

    // Context A: đăng ký + tạo todo riêng tư
    await registerUser(pageA, emailA);
    await pageA.getByRole("button", { name: "Add Todo" }).click();
    await pageA.locator("#title").fill("A's Private Todo");
    await pageA.getByRole("button", { name: "Create" }).click();
    await expect(pageA.getByText("A's Private Todo")).toBeVisible();

    // Context B: đăng ký user khác hoàn toàn (tab riêng, cookie/storage riêng)
    await registerUser(pageB, emailB);

    // Assert: User B KHÔNG thấy todo của User A
    await expect(pageB.getByText("A's Private Todo")).not.toBeVisible();
  } finally {
    // Dọn dẹp dù test pass hay fail
    await contextA.close();
    await contextB.close();
  }
});
