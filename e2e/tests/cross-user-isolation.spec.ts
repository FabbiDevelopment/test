import { test, expect } from "@playwright/test";
import { register, createTodo } from "./helpers";

test("one user cannot list or update another user's todo", async ({ browser }) => {
  const contextA = await browser.newContext();
  const contextB = await browser.newContext();
  try {
    const a = await contextA.newPage();
    const b = await contextB.newPage();
    await register(a);
    await createTodo(a, "A private todo");
    const tokenA = await a.evaluate(() => localStorage.getItem("access_token"));
    const apiUrl = (process.env.E2E_API_URL || "http://localhost:8000") + "/api/v1/todos";
    const aTodos = await a.request.get(apiUrl, { headers: { Authorization: `Bearer ${tokenA}` } });
    const todoId = (await aTodos.json()).items[0].id;
    await register(b);
    await expect(b.getByText("A private todo", { exact: true })).toHaveCount(0);
    const tokenB = await b.evaluate(() => localStorage.getItem("access_token"));
    const update = await b.request.put(`${apiUrl}/${todoId}`, {
      headers: { Authorization: `Bearer ${tokenB}` }, data: { title: "Stolen" },
    });
    expect(update.status()).toBe(403);
  } finally {
    await contextA.close();
    await contextB.close();
  }
});
