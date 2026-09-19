import { expect, test } from "@playwright/test";

test("renders a FastAPI validation error without crashing the registration form", async ({
  page,
}) => {
  const validationMessage = "The email address is not valid";
  const pageErrors: Error[] = [];
  page.on("pageerror", (error) => pageErrors.push(error));

  await page.route("**/api/v1/auth/register", (route) =>
    route.fulfill({
      status: 422,
      contentType: "application/json",
      body: JSON.stringify({
        detail: [
          {
            loc: ["body", "email"],
            msg: validationMessage,
            type: "value_error",
          },
        ],
      }),
    }),
  );

  await page.goto("/register");
  await page.getByLabel("Email").fill("fe009@example.com");
  await page.getByLabel("Password", { exact: true }).fill("password123");
  await page.getByLabel("Confirm Password").fill("password123");
  await page.getByRole("button", { name: "Create Account" }).click();

  await expect(page.getByText(validationMessage)).toBeVisible();
  expect(pageErrors).toEqual([]);
});
