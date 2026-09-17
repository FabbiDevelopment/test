import { test, expect } from "@playwright/test";

test("register, login, create todo, toggle and logout", async ({ page }) => {
    const email = `e2e-${Date.now()}@test.com`;
    const password = "Password123!";

    // Register
    await page.goto("/register");

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password", { exact: true }).fill(password);
    await page.getByLabel("Confirm Password", { exact: true }).fill(password);

    await page.getByRole("button", { name: "Create Account" }).click();

    // Login
    // Login
    await expect(page).toHaveURL(/\/$/);
    await page.goto("/login");

    await page.getByLabel("Email").fill(email);
    await page.getByLabel("Password").fill(password);

    await page.getByRole("button", { name: "Sign In" }).click();

    // Todo page
    await expect(page).toHaveURL(/\/$/);
    // Open create todo form
    await page.getByRole("button", { name: "Add Todo" }).click();

    // Create todo
    const todoTitle = `E2E Todo ${Date.now()}`;

    await page.getByPlaceholder("What needs to be done?").fill(todoTitle);
    await page.getByRole("button", { name: "Create", exact: true }).click();

    // Verify todo appears
    const todo = page.getByText(todoTitle, { exact: true });
    await expect(todo).toBeVisible();

    // Toggle completed
    // Toggle completed
    const checkbox = page.getByRole("checkbox", { name: todoTitle });

    await checkbox.click();

    await expect(checkbox).toBeChecked();

    // Verify completed state
    await expect(checkbox).toBeChecked();

    // Logout
    await page.getByRole("button", { name: "Logout" }).click();

    await expect(page).toHaveURL(/\/login/);
});


test("user cannot see another user's todo", async ({ browser }) => {
    const userA = {
        email: `e2e-a-${Date.now()}@test.com`,
        password: "Password123!",
    };

    const userB = {
        email: `e2e-b-${Date.now()}@test.com`,
        password: "Password123!",
    };

    const todoTitle = `Private Todo ${Date.now()}`;

    // User A - register
    const contextA = await browser.newContext();
    const pageA = await contextA.newPage();

    await pageA.goto("/register");

    await pageA.getByLabel("Email").fill(userA.email);
    await pageA.getByLabel("Password", { exact: true }).fill(userA.password);
    await pageA.getByLabel("Confirm Password", { exact: true }).fill(userA.password);

    await pageA.getByRole("button", { name: "Create Account" }).click();
    await expect(pageA).toHaveURL(/\/$/);
    await pageA.goto("/login");

    // User A - login
    await pageA.getByLabel("Email").fill(userA.email);
    await pageA.getByLabel("Password").fill(userA.password);
    await pageA.getByRole("button", { name: "Sign In" }).click();

    await expect(pageA).toHaveURL(/\/$/);
    await expect(
        pageA.getByRole("button", { name: "Add Todo" }),
    ).toBeVisible();

    // User A - create private todo
    await pageA.getByRole("button", { name: "Add Todo" }).click();

    await pageA.getByPlaceholder("What needs to be done?").fill(todoTitle);
    await pageA.getByRole("button", { name: "Create", exact: true }).click();

    await expect(
        pageA.getByText(todoTitle, { exact: true }),
    ).toBeVisible();

    // User B - separate browser session
    const contextB = await browser.newContext();
    const pageB = await contextB.newPage();

    await pageB.goto("/register");

    await pageB.getByLabel("Email").fill(userB.email);
    await pageB.getByLabel("Password", { exact: true }).fill(userB.password);
    await pageB.getByLabel("Confirm Password", { exact: true }).fill(userB.password);

    await pageB.getByRole("button", { name: "Create Account" }).click();
    await pageB.goto("/login");

    // User B - login
    await pageB.getByLabel("Email").fill(userB.email);
    await pageB.getByLabel("Password").fill(userB.password);
    await pageB.getByRole("button", { name: "Sign In" }).click();

    // User B must not see User A's todo
    await expect(
        pageB.getByText(todoTitle, { exact: true }),
    ).not.toBeVisible();

    await contextA.close();
    await contextB.close();
});