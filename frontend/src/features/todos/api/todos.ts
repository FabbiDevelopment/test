import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "@/features/tags/api/tags";

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  tags: Tag[];
}

interface TodoListResponse {
  items: Todo[];
  total: number;
  page: number;
  size: number;
}

interface CreateTodoRequest {
  title: string;
  description?: string;
}

interface UpdateTodoRequest {
  title?: string;
  description?: string;
  completed?: boolean;
}

export interface TodoFilters {
  status?: "completed" | "active";
  tagId?: string;
  keyword?: string;
  dateFrom?: string; // YYYY-MM-DD
  dateTo?: string; // YYYY-MM-DD
}

export const EMPTY_FILTERS: TodoFilters = {};

interface BulkStatusResult {
  updated_ids: string[];
  skipped_ids: string[];
}

// The query key embeds every filter parameter (page/size + all of
// TodoFilters), so two different filter combinations are cached
// independently and never collide - per the README's requirement that
// "Query keys must include all filter parameters."
export function todosQueryKey(page: number, size: number, filters: TodoFilters) {
  return [
    "todos",
    "list",
    page,
    size,
    filters.status ?? null,
    filters.tagId ?? null,
    filters.keyword ?? null,
    filters.dateFrom ?? null,
    filters.dateTo ?? null,
  ] as const;
}

export function useTodos(
  page: number = 1,
  size: number = 20,
  filters: TodoFilters = EMPTY_FILTERS
) {
  return useQuery({
    queryKey: todosQueryKey(page, size, filters),
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: {
          page,
          size,
          status: filters.status,
          tag_id: filters.tagId,
          keyword: filters.keyword || undefined,
          date_from: filters.dateFrom || undefined,
          date_to: filters.dateTo || undefined,
        },
      });
      return response.data;
    },
    placeholderData: (previousData) => previousData,
  });
}

// Any write invalidates every cached filter combination for the "todos"
// list - TanStack Query's invalidateQueries does prefix matching, so
// invalidating ["todos", "list"] catches every page/filter variant above.
function invalidateAllTodoLists() {
  queryClient.invalidateQueries({ queryKey: ["todos", "list"] });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: () => {
      invalidateAllTodoLists();
      toast.success("Todo created successfully!");
    },
    onError: () => {
      toast.error("Failed to create todo");
    },
  });
}

export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: UpdateTodoRequest;
    }): Promise<Todo> => {
      const response = await api.put(`/todos/${id}`, data);
      return response.data;
    },
    onError: () => {
      toast.error("Failed to update todo");
    },
    onSettled: () => {
      invalidateAllTodoLists();
    },
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      invalidateAllTodoLists();
      toast.success("Todo deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete todo");
    },
  });
}

export function useToggleTodo() {
  const updateTodo = useUpdateTodo();

  return {
    ...updateTodo,
    mutate: (todo: Todo) => {
      updateTodo.mutate({
        id: todo.id,
        data: { completed: !todo.completed },
      });
    },
  };
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async ({
      todoIds,
      completed,
    }: {
      todoIds: string[];
      completed: boolean;
    }): Promise<BulkStatusResult> => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids: todoIds,
        completed,
      });
      return response.data;
    },
    onSuccess: (result) => {
      invalidateAllTodoLists();
      toast.success(
        `Updated ${result.updated_ids.length} todo${
          result.updated_ids.length === 1 ? "" : "s"
        }${result.skipped_ids.length ? ` (${result.skipped_ids.length} skipped)` : ""}`
      );
    },
    onError: () => {
      toast.error("Failed to update selected todos");
    },
  });
}
