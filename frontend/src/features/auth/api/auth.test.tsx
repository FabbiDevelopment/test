import { describe, expect, it, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { useLogout } from "./auth";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

vi.mock("@/lib/api", () => ({
  api: {
    post: vi.fn(),
  },
}));

function wrapper({ children }: { children: React.ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe("useLogout (cache invalidation after logout)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    localStorage.setItem("access_token", "fake-access-token");
    localStorage.setItem("refresh_token", "fake-refresh-token");
    // Simulate data left over from a previous user's session.
    queryClient.setQueryData(["todos", "list", 1, 20, null, null, null, null, null], {
      items: [{ id: "1", title: "Previous user's todo" }],
    });
    queryClient.setQueryData(["auth", "me"], { email: "previous-user@example.com" });
  });

  it("clears both localStorage tokens and every cached query on successful logout", async () => {
    (api.post as ReturnType<typeof vi.fn>).mockResolvedValue({ data: {} });

    const { result } = renderHook(() => useLogout(), { wrapper });

    expect(localStorage.getItem("access_token")).toBe("fake-access-token");
    expect(queryClient.getQueryData(["auth", "me"])).toBeDefined();

    result.current.mutate();

    await waitFor(() => expect(result.current.isSuccess).toBe(true));

    expect(localStorage.getItem("access_token")).toBeNull();
    expect(localStorage.getItem("refresh_token")).toBeNull();
    expect(queryClient.getQueryData(["auth", "me"])).toBeUndefined();
    expect(
      queryClient.getQueryData(["todos", "list", 1, 20, null, null, null, null, null])
    ).toBeUndefined();
  });
});
