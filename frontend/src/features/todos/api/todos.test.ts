import { describe, expect, it } from "vitest";
import { todosQueryKey } from "./todos";

describe("todosQueryKey (filter query key uniqueness)", () => {
  it("produces the same key for the same page/size/filters", () => {
    const a = todosQueryKey(1, 20, { status: "active" });
    const b = todosQueryKey(1, 20, { status: "active" });
    expect(a).toEqual(b);
  });

  it("produces a different key for a different page", () => {
    const a = todosQueryKey(1, 20, {});
    const b = todosQueryKey(2, 20, {});
    expect(a).not.toEqual(b);
  });

  it("produces a different key for a different status filter", () => {
    const active = todosQueryKey(1, 20, { status: "active" });
    const completed = todosQueryKey(1, 20, { status: "completed" });
    const none = todosQueryKey(1, 20, {});
    expect(active).not.toEqual(completed);
    expect(active).not.toEqual(none);
    expect(completed).not.toEqual(none);
  });

  it("produces a different key for a different tag filter", () => {
    const a = todosQueryKey(1, 20, { tagId: "tag-1" });
    const b = todosQueryKey(1, 20, { tagId: "tag-2" });
    expect(a).not.toEqual(b);
  });

  it("produces a different key for a different keyword", () => {
    const a = todosQueryKey(1, 20, { keyword: "milk" });
    const b = todosQueryKey(1, 20, { keyword: "eggs" });
    expect(a).not.toEqual(b);
  });

  it("produces a different key for a different date range", () => {
    const a = todosQueryKey(1, 20, { dateFrom: "2026-01-01" });
    const b = todosQueryKey(1, 20, { dateFrom: "2026-02-01" });
    expect(a).not.toEqual(b);
  });

  it("combining multiple filters still yields a distinct, stable key", () => {
    const combo = { status: "active" as const, tagId: "t1", keyword: "milk" };
    const a = todosQueryKey(1, 20, combo);
    const b = todosQueryKey(1, 20, combo);
    const different = todosQueryKey(1, 20, { ...combo, keyword: "eggs" });
    expect(a).toEqual(b);
    expect(a).not.toEqual(different);
  });
});
