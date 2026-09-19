import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string;
  name: string;
  color?: string | null;
  user_id: string;
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
  tags?: Tag[];
}

export interface TodoListResponse {
  items: Todo[];
  total: number;
  page: number;
  size: number;
}

export interface TodoFilterParams {
  page?: number;
  size?: number;
  status?: string;
  keyword?: string;
  tag_id?: string;
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

export function useTodos(params: TodoFilterParams = { page: 1, size: 10000 }) {
  return useQuery({
    queryKey: ["todos", params],
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: {
          page: params.page || 1,
          size: params.size || 10000,
          status: params.status && params.status !== "all" ? params.status : undefined,
          keyword: params.keyword || undefined,
          tag_id: params.tag_id && params.tag_id !== "all" ? params.tag_id : undefined,
        },
      });
      return response.data;
    },
  });
}

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: { name: string; color?: string }): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag created!");
    },
    onError: (err: any) => {
      toast.error(err.response?.data?.detail || "Failed to create tag");
    },
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (tagId: string): Promise<void> => {
      await api.delete(`/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag deleted!");
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
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previousTodos = queryClient.getQueriesData<TodoListResponse>({
        queryKey: ["todos"],
      });

      queryClient.setQueriesData<TodoListResponse>(
        { queryKey: ["todos"] },
        (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((todo) =>
              todo.id === id ? { ...todo, ...data } : todo
            ),
          };
        }
      );

      return { previousTodos };
    },
    onError: (_err, _vars, context) => {
      if (context?.previousTodos) {
        context.previousTodos.forEach(([key, data]) => {
          queryClient.setQueryData(key, data);
        });
      }
      toast.error("Failed to update todo");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async ({
      todo_ids,
      completed,
    }: {
      todo_ids: string[];
      completed: boolean;
    }) => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids,
        completed,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Bulk update successful!");
    },
    onError: () => {
      toast.error("Failed to perform bulk update");
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
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }) => {
      const response = await api.delete(`/todos/${todo_id}/tags/${tag_id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag removed!");
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
