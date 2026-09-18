import { randomUUID } from "node:crypto";
import { expect, type Page } from "@playwright/test";

export const password = "Password@123";

export async function register(page: Page) {
  const email = `e2e-${randomUUID()}@example.com`;
  await page.goto("/register");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByLabel("Confirm Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Create Account", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Todo App" })).toBeVisible();
  await expect(page.getByTestId("pagination")).toContainText("0 total");
  return email;
}

export async function createTodo(page: Page, title: string) {
  await page.getByRole("button", { name: "Add Todo", exact: true }).click();
  const form = page.getByRole("dialog");
  await form.getByLabel("Title", { exact: true }).fill(title);
  await form.getByLabel("Description (optional)").fill("Description survives updates");
  await form.getByRole("button", { name: "Create", exact: true }).click();
  await expect(form).not.toBeVisible();
  await expect(page.getByTestId("todo-item").filter({ hasText: title })).toBeVisible();
}

export async function login(page: Page, email: string) {
  await page.goto("/login");
  await page.getByLabel("Email", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Sign In", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Todo App" })).toBeVisible();
  await expect(page.getByTestId("pagination")).toBeVisible();
}
