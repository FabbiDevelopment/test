import { test, expect } from "@playwright/test";

/**
 * E2E Scenario 2 — Cross-user data isolation (Cách ly dữ liệu giữa users)
 * User A tạo todo riêng tư → User B login → todo KHÔNG hiển thị.
 */
test.describe("Cross-user data isolation", () => {
  const timestamp = Date.now();
  const userA = {
    email: `e2e-usera-${timestamp}@test.com`,
    password: "password123",
  };
  const userB = {
    email: `e2e-userb-${timestamp}@test.com`,
    password: "password123",
  };
  const privateTodoTitle = `Private Todo ${timestamp}`;

  test("User B must not see User A private todo", async ({ browser }) => {
    // Context A — Phiên trình duyệt riêng cho User A
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    await pageA.goto("/register");
    await pageA.getByLabel("Email").fill(userA.email);
    await pageA.getByLabel("Password", { exact: true }).fill(userA.password);
    await pageA.getByLabel("Confirm Password").fill(userA.password);
    await pageA.getByRole("button", { name: "Create Account" }).click();
    await expect(pageA.getByText("My Todos")).toBeVisible({ timeout: 10_000 });

    // User A tạo todo riêng tư
    await pageA.getByRole("button", { name: "Add Todo" }).click();
    await pageA.getByLabel("Title").fill(privateTodoTitle);
    await pageA.getByRole("button", { name: "Create" }).click();
    await expect(pageA.getByText(privateTodoTitle)).toBeVisible();

    // User A logout
    await pageA.getByRole("button", { name: "Logout" }).click();
    await expect(pageA.getByRole("button", { name: "Sign In" })).toBeVisible();
    await contextA.close();

    // Context B — Phiên trình duyệt riêng cho User B (isolated storage)
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    await pageB.goto("/register");
    await pageB.getByLabel("Email").fill(userB.email);
    await pageB.getByLabel("Password", { exact: true }).fill(userB.password);
    await pageB.getByLabel("Confirm Password").fill(userB.password);
    await pageB.getByRole("button", { name: "Create Account" }).click();
    await expect(pageB.getByText("My Todos")).toBeVisible({ timeout: 10_000 });

    // User B KHÔNG thấy todo của User A — data isolation check
    await expect(pageB.getByText(privateTodoTitle)).not.toBeVisible();

    await contextB.close();
  });
});
