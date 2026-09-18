import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color: string | null;
  created_at: string;
  updated_at: string;
}

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
  status: "all" | "active" | "completed";
  tag_id: string;
  keyword: string;
  date_from: string;
  date_to: string;
  page: number;
  page_size: number;
}

export const defaultTodoFilters: TodoFilters = {
  status: "all",
  tag_id: "",
  keyword: "",
  date_from: "",
  date_to: "",
  page: 1,
  page_size: 100,
};

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

const invalidateTodos = () =>
  queryClient.invalidateQueries({ queryKey: ["todos"] });

export function useTodos(filters: TodoFilters) {
  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async (): Promise<TodoListResponse> => {
      const params = Object.fromEntries(
        Object.entries(filters).filter(([, value]) => value !== "")
      );
      if (filters.date_from) params.date_from = `${filters.date_from}T00:00:00Z`;
      if (filters.date_to) params.date_to = `${filters.date_to}T23:59:59Z`;
      const response = await api.get("/todos", { params });
      return response.data;
    },
  });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> =>
      (await api.post("/todos", data)).data,
    onSuccess: () => {
      invalidateTodos();
      toast.success("Todo created successfully!");
    },
    onError: () => toast.error("Failed to create todo"),
  });
}

export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateTodoRequest }) =>
      (await api.put<Todo>(`/todos/${id}`, data)).data,
    onSuccess: invalidateTodos,
    onError: () => toast.error("Failed to update todo"),
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/todos/${id}`),
    onSuccess: () => {
      invalidateTodos();
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
      updateTodo.mutate({ id: todo.id, data: { completed: !todo.completed } }),
  };
}

export function useBulkStatus() {
  return useMutation({
    mutationFn: async ({ todoIds, completed }: { todoIds: string[]; completed: boolean }) =>
      api.patch("/todos/bulk-status", { todo_ids: todoIds, completed }),
    onSuccess: () => {
      invalidateTodos();
      toast.success("Selected todos updated");
    },
    onError: () => toast.error("Bulk update failed"),
  });
}

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data,
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: { name: string; color?: string }) =>
      (await api.post<Tag>("/tags", data)).data,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["tags"] }),
    onError: () => toast.error("Could not create tag"),
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { name?: string; color?: string } }) =>
      (await api.patch<Tag>(`/tags/${id}`, data)).data,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      invalidateTodos();
    },
    onError: () => toast.error("Could not update tag"),
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string) => api.delete(`/tags/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      invalidateTodos();
    },
    onError: () => toast.error("Could not delete tag"),
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) =>
      api.post(`/todos/${todoId}/tags`, { tag_id: tagId }),
    onSuccess: invalidateTodos,
    onError: () => toast.error("Could not attach tag"),
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) =>
      api.delete(`/todos/${todoId}/tags/${tagId}`),
    onSuccess: invalidateTodos,
    onError: () => toast.error("Could not remove tag"),
  });
}
