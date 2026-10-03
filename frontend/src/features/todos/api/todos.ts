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

export interface TodoListResponse {
  items: Todo[];
  total: number;
  page: number;
  size: number;
}

export interface CreateTodoRequest {
  title: string;
  description?: string;
}

export interface UpdateTodoRequest {
  title?: string;
  description?: string;
  completed?: boolean;
}

export interface TodoFilters {
  page?: number;
  size?: number;
  status?: "active" | "completed" | "";
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
}

export function useTodos(filters: TodoFilters = {}) {
  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async (): Promise<TodoListResponse> => {
      // Clean up empty filters
      const params = Object.fromEntries(
        Object.entries(filters).filter(([_, v]) => v !== undefined && v !== "")
      );
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

export function useBulkUpdateTodos() {
  return useMutation({
    mutationFn: async (data: { todo_ids: string[]; completed: boolean }) => {
      const response = await api.patch("/todos/bulk-status", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todos updated successfully!");
    },
    onError: () => {
      toast.error("Failed to bulk update todos");
    },
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }) => {
      const response = await api.post(`/todos/${todo_id}/tags`, { tag_id });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to attach tag");
    },
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }) => {
      await api.delete(`/todos/${todo_id}/tags/${tag_id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag detached!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to detach tag");
    },
  });
}
