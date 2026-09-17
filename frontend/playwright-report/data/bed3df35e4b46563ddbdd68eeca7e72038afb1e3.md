# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: todo.spec.ts >> register, login, create todo, toggle and logout
- Location: tests\todo.spec.ts:3:1

# Error details

```
Error: locator.fill: Error: strict mode violation: getByLabel('Password') resolved to 2 elements:
    1) <input id="password" type="password" name="password" data-slot="input" placeholder="••••••••" class="h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none selection:bg-primary selection:text-primary-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-allowed disabled:…/> aka getByRole('textbox', { name: 'Password', exact: true })
    2) <input type="password" data-slot="input" id="confirmPassword" placeholder="••••••••" name="confirmPassword" class="h-9 w-full min-w-0 rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-xs transition-[color,box-shadow] outline-none selection:bg-primary selection:text-primary-foreground file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground disabled:pointer-events-none disabled:cursor-not-all…/> aka getByRole('textbox', { name: 'Confirm Password' })

Call log:
  - waiting for getByLabel('Password')

```

# Page snapshot

```yaml
- generic [ref=e2]:
  - generic [ref=e5]:
    - generic [ref=e6]:
      - heading "Create Account" [level=1] [ref=e7]
      - paragraph [ref=e8]: Sign up for a new account
    - generic [ref=e9]:
      - generic [ref=e10]:
        - generic [ref=e11] [cursor=pointer]: Email
        - textbox "Email" [active] [ref=e12]:
          - /placeholder: you@example.com
          - text: e2e-1789619915050@test.com
      - generic [ref=e13]:
        - generic [ref=e14] [cursor=pointer]: Password
        - textbox "Password" [ref=e15]:
          - /placeholder: ••••••••
      - generic [ref=e16]:
        - generic [ref=e17] [cursor=pointer]: Confirm Password
        - textbox "Confirm Password" [ref=e18]:
          - /placeholder: ••••••••
      - button "Create Account" [ref=e19] [cursor=pointer]
      - paragraph [ref=e20]:
        - text: Already have an account?
        - link "Sign in" [ref=e21] [cursor=pointer]:
          - /url: /login
  - region "Notifications alt+T"
```

# Test source

```ts
  1  | import { test, expect } from "@playwright/test";
  2  | 
  3  | test("register, login, create todo, toggle and logout", async ({ page }) => {
  4  |   const email = `e2e-${Date.now()}@test.com`;
  5  |   const password = "Password123!";
  6  | 
  7  |   // Register
  8  |   await page.goto("/register");
  9  | 
  10 |   await page.getByLabel("Email").fill(email);
> 11 |   await page.getByLabel("Password").fill(password);
     |                                     ^ Error: locator.fill: Error: strict mode violation: getByLabel('Password') resolved to 2 elements:
  12 |   await page.getByLabel("Confirm Password").fill(password);
  13 | 
  14 |   await page.getByRole("button", { name: "Create Account" }).click();
  15 | 
  16 |   // Login
  17 |   await expect(page).toHaveURL(/\/login/);
  18 | 
  19 |   await page.getByLabel("Email").fill(email);
  20 |   await page.getByLabel("Password").fill(password);
  21 | 
  22 |   await page.getByRole("button", { name: "Sign In" }).click();
  23 | 
  24 |   // Todo page
  25 |   await expect(page).toHaveURL(/\/todos/);
  26 | 
  27 |   // Open create todo form
  28 |   await page.getByRole("button", { name: "Add Todo" }).click();
  29 | 
  30 |   // Create todo
  31 |   const todoTitle = `E2E Todo ${Date.now()}`;
  32 | 
  33 |   await page.getByPlaceholder("What needs to be done?").fill(todoTitle);
  34 |   await page.getByRole("button", { name: "Create", exact: true }).click();
  35 | 
  36 |   // Verify todo appears
  37 |   const todo = page.getByText(todoTitle, { exact: true });
  38 |   await expect(todo).toBeVisible();
  39 | 
  40 |   // Toggle completed
  41 |   const todoItem = todo.locator("..");
  42 |   const checkbox = todoItem.getByRole("checkbox");
  43 | 
  44 |   await checkbox.check();
  45 | 
  46 |   // Verify completed state
  47 |   await expect(checkbox).toBeChecked();
  48 | 
  49 |   // Logout
  50 |   await page.getByRole("button", { name: "Logout" }).click();
  51 | 
  52 |   await expect(page).toHaveURL(/\/login/);
  53 | });
```