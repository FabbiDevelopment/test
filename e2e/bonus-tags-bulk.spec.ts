import { expect, test, type Page } from "@playwright/test";

import { registerUser, uniqueEmail } from "./helpers/auth";

async function createTodo(page: Page, title: string) {
  await page.getByRole("button", { name: "Add Todo" }).click();
  await page.getByLabel("Title").fill(title);
  await page.getByRole("button", { name: "Create", exact: true }).click();
  await expect(page.getByText(title, { exact: true })).toBeVisible();
}

test("manage tags, filter todos, and bulk update status", async ({ page }) => {
  const firstTitle = `Urgent task ${Date.now()}`;
  const secondTitle = `Routine task ${Date.now()}`;
  await registerUser(page, uniqueEmail("bonus"));

  await page.getByRole("button", { name: "Manage Tags" }).click();
  await page.getByLabel("Tag name").fill("Urgent");
  await page.getByRole("button", { name: "Create tag" }).click();
  await expect(
    page.getByRole("dialog").getByText("Urgent", { exact: true }),
  ).toBeVisible();
  await page.keyboard.press("Escape");

  await createTodo(page, firstTitle);
  await createTodo(page, secondTitle);

  await page.getByLabel(`Tag for ${firstTitle}`).selectOption({ label: "Urgent" });
  await page.getByRole("button", { name: `Attach tag to ${firstTitle}` }).click();
  await expect(
    page.getByRole("button", { name: `Remove Urgent from ${firstTitle}` }),
  ).toBeVisible();

  await page.getByLabel("Tag", { exact: true }).selectOption({ label: "Urgent" });
  await expect(page.getByText(firstTitle, { exact: true })).toBeVisible();
  await expect(page.getByText(secondTitle, { exact: true })).toHaveCount(0);

  await page.getByRole("button", { name: "Clear filters" }).click();
  await page.getByRole("checkbox", { name: `Select ${firstTitle}` }).click();
  await page.getByRole("checkbox", { name: `Select ${secondTitle}` }).click();
  await page.getByRole("button", { name: "Mark completed" }).click();

  await expect(
    page.getByRole("checkbox", { name: firstTitle, exact: true }),
  ).toBeChecked();
  await expect(
    page.getByRole("checkbox", { name: secondTitle, exact: true }),
  ).toBeChecked();

  await page.getByLabel("Status").selectOption("completed");
  await page.getByLabel("Keyword").fill("Urgent task");
  await expect(page.getByText(firstTitle, { exact: true })).toBeVisible();
  await expect(page.getByText(secondTitle, { exact: true })).toHaveCount(0);
});
