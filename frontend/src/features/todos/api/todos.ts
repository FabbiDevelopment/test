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
  tags?: Tag[];
}

export interface TodoFilters {
  keyword?: string;
  status?: boolean;
  tag_id?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  size?: number;
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

interface BulkStatusRequest {
  todo_ids: string[];
  completed: boolean;
}

export function useTodos(filters: TodoFilters = {}) {
  const page = filters.page || 1;
  const size = filters.size || 10000;

  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async (): Promise<TodoListResponse> => {
      const params: Record<string, any> = { page, size };
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.status !== undefined) params.status = filters.status;
      if (filters.tag_id) params.tag_id = filters.tag_id;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;

      const response = await api.get("/todos", { params });
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
    onError: () => {
      toast.error("Failed to update todo");
    },
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todo deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete todo");
    },
  });
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async (data: BulkStatusRequest): Promise<{ updated_count: number }> => {
      const response = await api.patch("/todos/bulk-status", data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(`Updated ${data.updated_count} todos successfully!`);
    },
    onError: () => {
      toast.error("Failed to update todos status");
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
