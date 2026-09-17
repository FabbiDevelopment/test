import { expect, test } from "@playwright/test";

import { registerUser, uniqueEmail } from "./helpers/auth";

test("user B cannot see user A private todo", async ({ browser }) => {
  const userAContext = await browser.newContext();
  const userBContext = await browser.newContext();

  try {
    const userAPage = await userAContext.newPage();
    const userBPage = await userBContext.newPage();
    const privateTitle = `User A private todo ${Date.now()}`;

    await registerUser(userAPage, uniqueEmail("user-a"));
    await userAPage.getByRole("button", { name: "Add Todo" }).click();
    await userAPage.getByLabel("Title").fill(privateTitle);
    await userAPage
      .getByRole("button", { name: "Create", exact: true })
      .click();

    await expect(
      userAPage.getByText(privateTitle, { exact: true }),
    ).toBeVisible();

    // A separate browser context has isolated cookies and localStorage.
    await registerUser(userBPage, uniqueEmail("user-b"));
    await expect(
      userBPage.getByText(privateTitle, { exact: true }),
    ).toHaveCount(0);

    // Reload to ensure the assertion also covers a fresh request to the API.
    await userBPage.reload();
    await expect(
      userBPage.getByText(privateTitle, { exact: true }),
    ).toHaveCount(0);
  } finally {
    await userAContext.close();
    await userBContext.close();
  }
});
