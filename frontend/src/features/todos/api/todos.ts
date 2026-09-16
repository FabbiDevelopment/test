import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "./tags";

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

export interface TodoFilters {
  page: number;
  pageSize: number;
  status: "" | "active" | "completed";
  tagId: string;
  keyword: string;
  dateFrom: string;
  dateTo: string;
}

export interface TodoListResponse {
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

export const defaultTodoFilters: TodoFilters = {
  page: 1,
  pageSize: 20,
  status: "",
  tagId: "",
  keyword: "",
  dateFrom: "",
  dateTo: "",
};

export const todoKeys = {
  all: ["todos"] as const,
  list: (filters: TodoFilters) => ["todos", "list", filters] as const,
};

function invalidateTodos() {
  return queryClient.invalidateQueries({ queryKey: todoKeys.all });
}

export function useTodos(filters: TodoFilters) {
  return useQuery({
    queryKey: todoKeys.list(filters),
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: {
          page: filters.page,
          page_size: filters.pageSize,
          status: filters.status || undefined,
          tag_id: filters.tagId || undefined,
          keyword: filters.keyword.trim() || undefined,
          date_from: filters.dateFrom
            ? new Date(`${filters.dateFrom}T00:00:00`).toISOString()
            : undefined,
          date_to: filters.dateTo
            ? new Date(`${filters.dateTo}T23:59:59.999`).toISOString()
            : undefined,
        },
      });
      return response.data;
    },
  });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: async () => {
      await invalidateTodos();
      toast.success("Todo created successfully!");
    },
    onError: () => toast.error("Failed to create todo"),
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
    onSuccess: invalidateTodos,
    onError: () => toast.error("Failed to update todo"),
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: async () => {
      await invalidateTodos();
      toast.success("Todo deleted successfully!");
    },
    onError: () => toast.error("Failed to delete todo"),
  });
}

export function useToggleTodo() {
  const updateTodo = useUpdateTodo();
  return {
    ...updateTodo,
    mutate: (todo: Todo) =>
      updateTodo.mutate({
        id: todo.id,
        data: { completed: !todo.completed },
      }),
  };
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      const response = await api.post(`/todos/${todoId}/tags`, {
        tag_id: tagId,
      });
      return response.data as Todo;
    },
    onSuccess: invalidateTodos,
    onError: () => toast.error("Failed to attach tag"),
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: invalidateTodos,
    onError: () => toast.error("Failed to remove tag"),
  });
}

export function useBulkStatus() {
  return useMutation({
    mutationFn: async ({
      todoIds,
      completed,
    }: {
      todoIds: string[];
      completed: boolean;
    }) => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids: todoIds,
        completed,
      });
      return response.data as { updated_count: number; items: Todo[] };
    },
    onSuccess: async (data) => {
      await invalidateTodos();
      toast.success(`${data.updated_count} todos updated`);
    },
    onError: () => toast.error("Bulk update failed"),
  });
}
