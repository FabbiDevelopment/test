const TODO_QUERY_ROOT = ["todos"] as const;

// Keep the default aligned with the backend's maximum accepted page size.
export const DEFAULT_TODO_PAGE_SIZE = 100;

export interface TodoFilters {
  keyword?: string;
  status?: "all" | "active" | "completed";
  tagId?: string;
  dateFrom?: string;
  dateTo?: string;
}

export const DEFAULT_TODO_FILTERS: Required<TodoFilters> = {
  keyword: "",
  status: "all",
  tagId: "",
  dateFrom: "",
  dateTo: "",
};

export function normalizeTodoFilters(filters: TodoFilters = {}): Required<TodoFilters> {
  return {
    keyword: filters.keyword?.trim() ?? "",
    status: filters.status ?? "all",
    tagId: filters.tagId ?? "",
    dateFrom: filters.dateFrom ?? "",
    dateTo: filters.dateTo ?? "",
  };
}

export const todoKeys = {
  all: TODO_QUERY_ROOT,
  user: (userId: string) => [...TODO_QUERY_ROOT, userId] as const,
  list: (userId: string, page: number, size: number, filters: TodoFilters = {}) =>
    [
      ...TODO_QUERY_ROOT,
      userId,
      "list",
      { page, size, ...normalizeTodoFilters(filters) },
    ] as const,
};
