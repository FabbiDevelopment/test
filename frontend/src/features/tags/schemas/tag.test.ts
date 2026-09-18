import { describe, expect, it } from "vitest";
import { tagSchema } from "./tag";

describe("tagSchema (tag form validation)", () => {
  it("accepts a valid name with no color", () => {
    const result = tagSchema.safeParse({ name: "Work" });
    expect(result.success).toBe(true);
  });

  it("accepts a valid name with a color", () => {
    const result = tagSchema.safeParse({ name: "Work", color: "#ff0000" });
    expect(result.success).toBe(true);
  });

  it("rejects an empty name", () => {
    const result = tagSchema.safeParse({ name: "" });
    expect(result.success).toBe(false);
  });

  it("rejects a name that is only whitespace", () => {
    const result = tagSchema.safeParse({ name: "   " });
    expect(result.success).toBe(false);
  });

  it("trims surrounding whitespace from a valid name", () => {
    const result = tagSchema.safeParse({ name: "  Work  " });
    expect(result.success).toBe(true);
    if (result.success) {
      expect(result.data.name).toBe("Work");
    }
  });

  it("rejects a name longer than 50 characters (matches backend limit)", () => {
    const result = tagSchema.safeParse({ name: "a".repeat(51) });
    expect(result.success).toBe(false);
  });

  it("accepts a name exactly at the 50 character limit", () => {
    const result = tagSchema.safeParse({ name: "a".repeat(50) });
    expect(result.success).toBe(true);
  });

  it("rejects a color longer than 20 characters (matches backend limit)", () => {
    const result = tagSchema.safeParse({ name: "Work", color: "a".repeat(21) });
    expect(result.success).toBe(false);
  });
});
