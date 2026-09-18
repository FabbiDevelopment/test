import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string; user_id: string; name: string; color: string | null;
  created_at: string; updated_at: string;
}
export interface Todo {
  id: string; title: string; description: string | null; completed: boolean;
  user_id: string; created_at: string; updated_at: string; tags: Tag[];
}
export interface TodoListResponse {
  items: Todo[]; total: number; page: number; page_size: number;
}
export interface CreateTodoRequest { title: string; description?: string }
export interface UpdateTodoRequest { title?: string; description?: string; completed?: boolean }
export interface TodoFilters {
  page?: number; page_size?: number; status?: boolean; tag_id?: string;
  keyword?: string; date_from?: string; date_to?: string;
}

const refreshTodos = () => queryClient.invalidateQueries({ queryKey: ["todos"] });
const refreshTags = () => queryClient.invalidateQueries({ queryKey: ["tags"] });

export function useTodos(filters: TodoFilters = {}, enabled = true) {
  const params = { page: 1, page_size: 20, ...filters };
  return useQuery({
    queryKey: ["todos", params],
    enabled,
    queryFn: async ({ signal }): Promise<TodoListResponse> =>
      (await api.get("/todos", { params, signal })).data,
  });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => (await api.post("/todos", data)).data,
    onSuccess: async () => { await refreshTodos(); toast.success("Todo created successfully!"); },
    onError: () => toast.error("Failed to create todo"),
  });
}

export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateTodoRequest }): Promise<Todo> =>
      (await api.put(`/todos/${id}`, data)).data,
    // Re-fetch all filter variants: a status/title change can move items between pages.
    // Keep the current data on failure instead of editing an unrelated exact cache key.
    onSuccess: refreshTodos,
    onError: () => toast.error("Failed to update todo"),
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string) => { await api.delete(`/todos/${id}`); },
    onSuccess: async () => { await refreshTodos(); toast.success("Todo deleted!"); },
    onError: () => toast.error("Failed to delete todo"),
  });
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async (data: { todo_ids: string[]; completed: boolean }): Promise<Todo[]> =>
      (await api.patch("/todos/bulk-status", data)).data,
    onSuccess: async () => { await refreshTodos(); toast.success("Todos updated!"); },
    onError: () => toast.error("Bulk update failed. Your selection has been kept; try again."),
  });
}

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: async ({ signal }): Promise<Tag[]> => (await api.get("/tags", { signal })).data,
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: { name: string; color?: string }): Promise<Tag> => (await api.post("/tags", data)).data,
    onSuccess: async () => { await refreshTags(); toast.success("Tag created!"); },
    onError: () => toast.error("Could not create tag. Check that the name is unique."),
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: { name: string; color?: string } }): Promise<Tag> =>
      (await api.patch(`/tags/${id}`, data)).data,
    onSuccess: async () => { await Promise.all([refreshTags(), refreshTodos()]); },
    onError: () => toast.error("Could not update tag. Check that the name is unique."),
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string) => { await api.delete(`/tags/${id}`); },
    onSuccess: async () => { await Promise.all([refreshTags(), refreshTodos()]); toast.success("Tag deleted!"); },
    onError: () => toast.error("Failed to delete tag"),
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }): Promise<Tag[]> =>
      (await api.post(`/todos/${todo_id}/tags`, { tag_id })).data,
    onSuccess: refreshTodos,
    onError: () => toast.error("Failed to attach tag"),
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }) => {
      await api.delete(`/todos/${todo_id}/tags/${tag_id}`);
    },
    onSuccess: refreshTodos,
    onError: () => toast.error("Failed to detach tag"),
  });
}
