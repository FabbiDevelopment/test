import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag { id: string; name: string; color: string | null; created_at: string; updated_at: string; }
export interface Todo { id: string; title: string; description: string | null; completed: boolean; user_id: string; created_at: string; updated_at: string; tags: Tag[]; }
export interface TodoFilters { page?: number; size?: number; completed?: boolean; tag_id?: string; keyword?: string; date_from?: string; date_to?: string; }
interface TodoListResponse { items: Todo[]; total: number; page: number; size: number; }
interface TodoPayload { title?: string; description?: string; completed?: boolean; }

const todosKey = (filters: TodoFilters) => ["todos", localStorage.getItem("access_token") || "anonymous", filters] as const;
const refreshTodos = () => queryClient.invalidateQueries({ queryKey: ["todos"] });

export function useTodos(filters: TodoFilters = {}) {
  const normalized = { page: 1, size: 100, ...filters };
  return useQuery({
    queryKey: todosKey(normalized),
    queryFn: async (): Promise<TodoListResponse> => (await api.get("/todos", { params: normalized })).data,
  });
}

export function useCreateTodo() {
  return useMutation({ mutationFn: async (data: TodoPayload): Promise<Todo> => (await api.post("/todos", data)).data,
    onSuccess: () => { refreshTodos(); toast.success("Todo created successfully!"); }, onError: () => toast.error("Failed to create todo") });
}
export function useUpdateTodo() {
  return useMutation({ mutationFn: async ({ id, data }: { id: string; data: TodoPayload }): Promise<Todo> => (await api.put(`/todos/${id}`, data)).data,
    onSuccess: refreshTodos, onError: () => toast.error("Failed to update todo") });
}
export function useDeleteTodo() {
  return useMutation({ mutationFn: async (id: string) => { await api.delete(`/todos/${id}`); }, onSuccess: () => { refreshTodos(); toast.success("Todo deleted successfully!"); }, onError: () => toast.error("Failed to delete todo") });
}
export function useToggleTodo() { const update = useUpdateTodo(); return { ...update, mutate: (todo: Todo) => update.mutate({ id: todo.id, data: { completed: !todo.completed } }) }; }
export function useBulkStatus() {
  return useMutation({ mutationFn: async ({ todoIds, completed }: { todoIds: string[]; completed: boolean }) => api.patch("/todos/bulk-status", { todo_ids: todoIds, completed }),
    onSuccess: () => { refreshTodos(); toast.success("Todos updated"); }, onError: () => toast.error("Could not update selected todos") });
}
export function useAttachTag() { return useMutation({ mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => (await api.post(`/todos/${todoId}/tags`, { tag_id: tagId })).data, onSuccess: refreshTodos }); }
export function useDetachTag() { return useMutation({ mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }) => (await api.delete(`/todos/${todoId}/tags/${tagId}`)).data, onSuccess: refreshTodos }); }
