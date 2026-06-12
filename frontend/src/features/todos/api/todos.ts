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

interface TodoFilters {
  page?: number;
  size?: number;
  status?: string;
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
}

export function useTodos(filters: TodoFilters = {}) {
  const { page = 1, size = 20, ...rest } = filters;
  return useQuery({
    queryKey: ["todos", { page, size, ...rest }],
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: { page, size, ...rest },
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

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async ({ todo_ids, completed }: { todo_ids: string[]; completed: boolean }) => {
      const response = await api.patch("/todos/bulk-status", { todo_ids, completed });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todos updated successfully!");
    },
    onError: () => {
      toast.error("Failed to update todos");
    },
  });
}

export function useAddTagToTodo() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      const response = await api.post(`/todos/${todoId}/tags`, null, {
        params: { tag_id: tagId },
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
    onError: () => {
      toast.error("Failed to add tag");
    },
  });
}

export function useRemoveTagFromTodo() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
    onError: () => {
      toast.error("Failed to remove tag");
    },
  });
}
