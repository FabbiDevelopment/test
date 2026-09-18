import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag { id: string; user_id: string; name: string; color: string | null; created_at: string; updated_at: string; }
export interface Todo { id: string; title: string; description: string | null; completed: boolean; user_id: string; created_at: string; updated_at: string; tags: Tag[]; }
export interface TodoFilters { page: number; page_size: number; status?: "all" | "active" | "completed"; tag_id?: string; keyword?: string; date_from?: string; date_to?: string; }
interface TodoListResponse { items: Todo[]; total: number; page: number; size: number; }
interface CreateTodoRequest { title: string; description?: string; }
interface UpdateTodoRequest { title?: string; description?: string; completed?: boolean; }

const refreshTodos = () => queryClient.invalidateQueries({ queryKey: ["todos"] });
const refreshTags = () => queryClient.invalidateQueries({ queryKey: ["tags"] });

export function useTodos(filters: TodoFilters) {
  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async (): Promise<TodoListResponse> => (await api.get("/todos", { params: filters })).data,
  });
}
export function useTags() {
  return useQuery({ queryKey: ["tags"], queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data });
}
export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => (await api.post("/todos", data)).data,
    onSuccess: () => { refreshTodos(); toast.success("Todo created successfully!"); },
    onError: () => toast.error("Failed to create todo"),
  });
}
export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateTodoRequest }): Promise<Todo> => (await api.put(`/todos/${id}`, data)).data,
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previousTodos = queryClient.getQueriesData<TodoListResponse>({ queryKey: ["todos"] });
      queryClient.setQueriesData<TodoListResponse>({ queryKey: ["todos"] }, current => current ? ({ ...current, items: current.items.map(todo => todo.id === id ? { ...todo, ...data } : todo) }) : current);
      return { previousTodos };
    },
    onError: (_error, _variables, context) => { context?.previousTodos.forEach(([key, data]) => queryClient.setQueryData(key, data)); toast.error("Failed to update todo"); },
    onSettled: refreshTodos,
  });
}
export function useDeleteTodo() {
  return useMutation({ mutationFn: async (id: string) => { await api.delete(`/todos/${id}`); }, onSuccess: () => { refreshTodos(); toast.success("Todo deleted"); }, onError: () => toast.error("Failed to delete todo") });
}
export function useToggleTodo() {
  const update = useUpdateTodo();
  return { ...update, mutate: (todo: Todo) => update.mutate({ id: todo.id, data: { completed: !todo.completed } }) };
}
export function useCreateTag() {
  return useMutation({ mutationFn: async (data: { name: string; color?: string }) => (await api.post("/tags", data)).data as Tag, onSuccess: () => { refreshTags(); toast.success("Tag created"); }, onError: () => toast.error("Tag name must be unique") });
}
export function useUpdateTag() {
  return useMutation({ mutationFn: async ({ id, data }: { id: string; data: { name?: string; color?: string } }) => (await api.patch(`/tags/${id}`, data)).data as Tag, onSuccess: () => { refreshTags(); refreshTodos(); }, onError: () => toast.error("Could not update tag") });
}
export function useDeleteTag() {
  return useMutation({ mutationFn: async (id: string) => api.delete(`/tags/${id}`), onSuccess: () => { refreshTags(); refreshTodos(); }, onError: () => toast.error("Could not delete tag") });
}
export function useSetTodoTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId, attached }: { todoId: string; tagId: string; attached: boolean }) => attached ? api.delete(`/todos/${todoId}/tags/${tagId}`) : api.post(`/todos/${todoId}/tags`, { tag_id: tagId }),
    onSuccess: refreshTodos, onError: () => toast.error("Could not update todo tags"),
  });
}
export function useBulkStatus() {
  return useMutation({
    mutationFn: async ({ todoIds, completed }: { todoIds: string[]; completed: boolean }) => api.patch("/todos/bulk-status", { todo_ids: todoIds, completed }),
    onSuccess: () => { refreshTodos(); toast.success("Todos updated"); },
    onError: () => toast.error("Bulk update failed"),
  });
}