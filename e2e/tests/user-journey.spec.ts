import { test, expect } from "@playwright/test";
import { register, login, createTodo } from "./helpers";

test("register, create, complete, reload, and log out", async ({ page }) => {
  const email = await register(page);
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await login(page, email);
  await createTodo(page, "Journey todo");
  const checkbox = page.getByRole("checkbox", { name: "Complete Journey todo", exact: true });
  await checkbox.click();
  await expect(checkbox).toBeChecked();
  await page.reload();
  await expect(checkbox).toBeChecked();
  await page.getByRole("button", { name: "Logout", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  expect(await page.evaluate(() => localStorage.getItem("access_token"))).toBeNull();
  expect(await page.evaluate(() => localStorage.getItem("refresh_token"))).toBeNull();
});
