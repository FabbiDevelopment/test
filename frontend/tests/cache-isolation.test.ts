import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

import {
  DEFAULT_TODO_PAGE_SIZE,
  todoKeys,
} from "../src/features/todos/api/queryKeys.js";
import { todoFiltersSchema } from "../src/features/todos/schemas/todo.js";
import {
  handleBulkStatusFailure,
  handleBulkStatusSuccess,
} from "../src/features/todos/api/mutationHandlers.js";
import { tagSchema } from "../src/features/tags/schemas/tag.js";
import { shouldClearSessionForUnauthorized } from "../src/lib/authErrorHandling.js";
import { getApiErrorMessage } from "../src/lib/apiError.js";
import { clearUserSession } from "../src/lib/sessionCleanup.js";
import { passwordSchema } from "../src/features/auth/schemas/auth.js";

test("todo list keys are isolated by user, pagination, and every filter", () => {
  const firstPage = todoKeys.list("user-a", 1, 20);

  assert.notDeepEqual(firstPage, todoKeys.list("user-b", 1, 20));
  assert.notDeepEqual(firstPage, todoKeys.list("user-a", 2, 20));
  assert.notDeepEqual(firstPage, todoKeys.list("user-a", 1, 50));

  const filterInputs = {
    keyword: "roadmap",
    status: "active" as const,
    tagId: "tag-a",
    dateFrom: "2026-01-01",
    dateTo: "2026-01-31",
  };
  const filtered = todoKeys.list("user-a", 1, 20, filterInputs);

  assert.notDeepEqual(
    filtered,
    todoKeys.list("user-a", 1, 20, { ...filterInputs, keyword: "launch" }),
  );
  assert.notDeepEqual(
    filtered,
    todoKeys.list("user-a", 1, 20, { ...filterInputs, status: "completed" }),
  );
  assert.notDeepEqual(
    filtered,
    todoKeys.list("user-a", 1, 20, { ...filterInputs, tagId: "tag-b" }),
  );
  assert.notDeepEqual(
    filtered,
    todoKeys.list("user-a", 1, 20, { ...filterInputs, dateFrom: "2026-02-01" }),
  );
});

test("default Todo page size is bounded by the API limit", () => {
  assert.equal(DEFAULT_TODO_PAGE_SIZE, 100);
});

test("Dashboard requests the selected Todo page and resets to page one for new filters", () => {
  const todoPageSource = readFileSync(
    "src/features/todos/components/TodoPage.tsx",
    "utf8",
  );

  assert.match(todoPageSource, /const \[page, setPage\] = useState\(1\)/);
  assert.match(todoPageSource, /useTodos\(\s*user\?\.id,\s*page,/);
  assert.match(todoPageSource, /setFilters\(nextFilters\);\s*setPage\(1\);/);
  assert.match(todoPageSource, /aria-label="Todo pagination"/);
  assert.match(todoPageSource, /aria-label="Previous page"/);
  assert.match(todoPageSource, /aria-label="Next page"/);
  assert.match(todoPageSource, /Page \{page\} of \{totalPages\}/);
});

test("Todo rows use their stable entity ID as the React key", () => {
  const todoListSource = readFileSync(
    "src/features/todos/components/TodoList.tsx",
    "utf8",
  );

  assert.match(todoListSource, /key=\{todo\.id\}/);
  assert.doesNotMatch(todoListSource, /key=\{index\}/);
});

test("each Todo row exposes only the multi-select checkbox", () => {
  const todoItemSource = readFileSync(
    "src/features/todos/components/TodoItem.tsx",
    "utf8",
  );

  assert.equal((todoItemSource.match(/<Checkbox/g) ?? []).length, 1);
  assert.match(todoItemSource, /aria-label="Select for bulk action"/);
  assert.match(todoItemSource, /onClick=\{\(\) => onToggle\(todo\)\}/);
  assert.match(todoItemSource, /Manage tags for \$\{todo\.title\}/);
  assert.match(todoItemSource, /onManageTags\(todo\.id\)/);
});

test("route pages are lazy loaded instead of inflating the entry bundle", () => {
  const routerSource = readFileSync("src/router/index.tsx", "utf8");

  assert.match(routerSource, /import\("@\/pages\/LoginPage"\)/);
  assert.match(routerSource, /import\("@\/pages\/RegisterPage"\)/);
  assert.match(routerSource, /import\("@\/pages\/DashboardPage"\)/);
  assert.match(routerSource, /<Suspense fallback=/);
});

test("Vite config remains compatible with its native config loader", () => {
  const viteConfigSource = readFileSync("vite.config.ts", "utf8");

  assert.match(viteConfigSource, /import\.meta\.dirname/);
  assert.doesNotMatch(viteConfigSource, /__dirname/);
});

test("Todo dialogs include a description for screen reader users", () => {
  const todoFormSource = readFileSync(
    "src/features/todos/components/TodoForm.tsx",
    "utf8",
  );

  assert.match(todoFormSource, /DialogDescription/);
  assert.match(todoFormSource, /Add a title and optional details/);
  assert.match(todoFormSource, /Update the title or details/);
});

test("API validation details are converted to a safe toast message", () => {
  const validationError = {
    isAxiosError: true,
    response: {
      data: {
        detail: [
          {
            loc: ["body", "email"],
            msg: "The email address is not valid",
            type: "value_error",
          },
        ],
      },
    },
  };

  assert.equal(
    getApiErrorMessage(validationError, "Registration failed."),
    "The email address is not valid",
  );
  assert.equal(
    getApiErrorMessage({ isAxiosError: true, response: { data: {} } }, "Fallback"),
    "Fallback",
  );
});

test("password validation matches the backend character and UTF-8 byte limits", () => {
  assert.equal(passwordSchema.safeParse("abcdef").success, true);
  assert.equal(passwordSchema.safeParse("short").success, false);
  assert.equal(passwordSchema.safeParse("😀".repeat(3)).success, false);
  assert.equal(passwordSchema.safeParse("😀".repeat(6)).success, true);
  assert.equal(passwordSchema.safeParse("😀".repeat(18)).success, true);
  assert.equal(passwordSchema.safeParse("😀".repeat(19)).success, false);
});

test("tag and date-range validation mirror backend constraints", () => {
  const normalizedTag = tagSchema.parse({ name: "  Planning  ", color: "#22c55e" });
  assert.deepEqual(normalizedTag, { name: "Planning", color: "#22c55e" });
  assert.equal(tagSchema.safeParse({ name: "   " }).success, false);
  assert.equal(tagSchema.safeParse({ name: "x".repeat(51) }).success, false);
  assert.equal(tagSchema.safeParse({ name: "Tag", color: "x".repeat(21) }).success, false);

  assert.equal(
    todoFiltersSchema.safeParse({
      keyword: "roadmap",
      status: "active",
      tagId: "tag-a",
      dateFrom: "2026-01-01",
      dateTo: "2026-01-31",
    }).success,
    true,
  );
  assert.equal(
    todoFiltersSchema.safeParse({
      keyword: "",
      status: "all",
      tagId: "",
      dateFrom: "2026-02-01",
      dateTo: "2026-01-31",
    }).success,
    false,
  );
});

test("bulk Todo success invalidates only the current user's lists and reports the result", async () => {
  const invalidatedKeys: (readonly unknown[])[] = [];
  const successMessages: string[] = [];
  const errorMessages: string[] = [];

  await handleBulkStatusSuccess(
    {
      invalidateQueries: async ({ queryKey }) => {
        invalidatedKeys.push(queryKey);
      },
    },
    {
      success: (message) => successMessages.push(message),
      error: (message) => errorMessages.push(message),
    },
    "user-a",
    { updated_count: 2, completed: true },
  );

  assert.deepEqual(invalidatedKeys, [todoKeys.user("user-a")]);
  assert.deepEqual(successMessages, ["2 todos marked completed"]);
  assert.deepEqual(errorMessages, []);
});

test("bulk Todo failure preserves the cache and exposes a useful error", () => {
  const messages: string[] = [];

  handleBulkStatusFailure(
    { success: () => undefined, error: (message) => messages.push(message) },
    "Todo not found",
  );

  assert.deepEqual(messages, ["Todo not found"]);
});

test("clearing a session removes tokens and all cached queries", () => {
  const removedKeys: string[] = [];
  let removeQueriesCalls = 0;

  clearUserSession(
    {
      removeItem: (key) => removedKeys.push(key),
    },
    {
      removeQueries: () => {
        removeQueriesCalls += 1;
      },
    }
  );

  assert.deepEqual(removedKeys, ["access_token", "refresh_token"]);
  assert.equal(removeQueriesCalls, 1);
});

test("login 401 stays with the form while protected requests clear the session", () => {
  assert.equal(shouldClearSessionForUnauthorized(401, "/auth/login"), false);
  assert.equal(
    shouldClearSessionForUnauthorized(401, "/auth/login?next=%2F"),
    false,
  );
  assert.equal(shouldClearSessionForUnauthorized(401, "/todos"), true);
  assert.equal(shouldClearSessionForUnauthorized(400, "/auth/login"), false);
});
