import { expect, test } from "@playwright/test";

import {
  loginUser,
  registerUser,
  TEST_PASSWORD,
  uniqueEmail,
} from "./helpers/auth";

test("register, login, create and complete a todo, then logout", async ({
  page,
}) => {
  const email = uniqueEmail("journey");
  const title = `Journey todo ${Date.now()}`;

  await registerUser(page, email);

  // Registration creates a session. Log out and sign in again to cover login too.
  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL("/login");
  await loginUser(page, email, TEST_PASSWORD);

  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill(title);
  await page.getByLabel("Description (optional)").fill("Created by Playwright");
  await page.getByRole("button", { name: "Create", exact: true }).click();

  await expect(page.getByText(title, { exact: true })).toBeVisible();

  const checkbox = page.getByRole("checkbox", { name: title, exact: true });
  await checkbox.click();
  await expect(checkbox).toBeChecked();

  // Reload to prove the completed state was persisted by the backend.
  await page.reload();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
  await expect(
    page.getByRole("checkbox", { name: title, exact: true }),
  ).toBeChecked();

  await page.getByRole("button", { name: "Logout" }).click();
  await expect(page).toHaveURL("/login");
});
