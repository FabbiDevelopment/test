import { expect, test } from "@playwright/test";
import { createTodoViaUI, registerViaUI, uniqueEmail } from "./helpers";

test.describe("Cross-user data isolation", () => {
  test("User B never sees User A's private todo", async ({ browser }) => {
    // Two fully independent sessions (separate localStorage/cookies), like
    // two different people on two different computers.
    const contextA = await browser.newContext();
    const contextB = await browser.newContext();
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();

    try {
      const emailA = uniqueEmail("owner");
      const emailB = uniqueEmail("intruder");
      const secretTitle = `A's private todo ${Date.now()}`;

      // User A registers and creates a private todo.
      await registerViaUI(pageA, emailA);
      await createTodoViaUI(pageA, secretTitle);
      await expect(pageA.getByText(secretTitle)).toBeVisible();

      // User B registers in a completely separate session.
      await registerViaUI(pageB, emailB);

      // User B's dashboard must not show User A's todo anywhere.
      await expect(pageB.getByText(secretTitle)).not.toBeVisible();
      await expect(pageB.getByText("No todos yet")).toBeVisible();

      // Defense in depth: even a direct API call as User B must not
      // return User A's todo (guards the IDOR regression at the API level,
      // not just "the UI didn't render it").
      const apiBase =
        process.env.E2E_API_URL ||
        new URL(pageB.url()).origin.replace(/:\d+$/, ":8000");
      const tokenB = await pageB.evaluate(() =>
        window.localStorage.getItem("access_token")
      );
      const listResponse = await pageB.request.get(`${apiBase}/api/v1/todos`, {
        headers: { Authorization: `Bearer ${tokenB}` },
      });
      const body = await listResponse.json();
      const titles = body.items.map((item: { title: string }) => item.title);
      expect(titles).not.toContain(secretTitle);
    } finally {
      await contextA.close();
      await contextB.close();
    }
  });
});
