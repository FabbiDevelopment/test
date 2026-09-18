import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BulkActionsBar } from "./BulkActionsBar";
import { api } from "@/lib/api";

vi.mock("@/lib/api", () => ({
  api: {
    patch: vi.fn(),
  },
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

function renderWithClient(ui: React.ReactElement) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>{ui}</QueryClientProvider>
  );
}

describe("BulkActionsBar (bulk action flow)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders nothing when no todos are selected", () => {
    const { container } = renderWithClient(
      <BulkActionsBar selectedIds={[]} onClear={() => {}} />
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("shows the selected count and action buttons when todos are selected", () => {
    renderWithClient(
      <BulkActionsBar selectedIds={["a", "b", "c"]} onClear={() => {}} />
    );
    expect(screen.getByText("3 selected")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /mark complete/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /mark active/i })).toBeInTheDocument();
  });

  it("calls the bulk-status API with the selected IDs when 'Mark complete' is clicked", async () => {
    (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { updated_ids: ["a", "b"], skipped_ids: [] },
    });
    const onClear = vi.fn();
    const user = userEvent.setup();

    renderWithClient(
      <BulkActionsBar selectedIds={["a", "b"]} onClear={onClear} />
    );

    await user.click(screen.getByRole("button", { name: /mark complete/i }));

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith("/todos/bulk-status", {
        todo_ids: ["a", "b"],
        completed: true,
      });
    });
    await waitFor(() => expect(onClear).toHaveBeenCalled());
  });

  it("calls the bulk-status API with completed:false when 'Mark active' is clicked", async () => {
    (api.patch as ReturnType<typeof vi.fn>).mockResolvedValue({
      data: { updated_ids: ["a"], skipped_ids: [] },
    });
    const user = userEvent.setup();

    renderWithClient(<BulkActionsBar selectedIds={["a"]} onClear={() => {}} />);

    await user.click(screen.getByRole("button", { name: /mark active/i }));

    await waitFor(() => {
      expect(api.patch).toHaveBeenCalledWith("/todos/bulk-status", {
        todo_ids: ["a"],
        completed: false,
      });
    });
  });

  it("clicking the clear (X) button calls onClear without hitting the API", async () => {
    const onClear = vi.fn();
    const user = userEvent.setup();

    renderWithClient(<BulkActionsBar selectedIds={["a"]} onClear={onClear} />);

    // The X button has no accessible name text, select by icon button position.
    const buttons = screen.getAllByRole("button");
    await user.click(buttons[buttons.length - 1]);

    expect(onClear).toHaveBeenCalled();
    expect(api.patch).not.toHaveBeenCalled();
  });
});
