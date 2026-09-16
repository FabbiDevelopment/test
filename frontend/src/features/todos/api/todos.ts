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
  status?: "all" | "active" | "completed";
  tag_id?: string;
  keyword?: string;
}

export function useTodos(filters?: TodoFilters, page: number = 1, size: number = 10000) {
  return useQuery({
    queryKey: ["todos", filters, page, size],
    queryFn: async (): Promise<TodoListResponse> => {
      const params: Record<string, any> = { page, size };
      if (filters?.status && filters.status !== "all") {
        params.status = filters.status;
      }
      if (filters?.tag_id) {
        params.tag_id = filters.tag_id;
      }
      if (filters?.keyword && filters.keyword.trim()) {
        params.keyword = filters.keyword.trim();
      }

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
    onMutate: async ({ id, data }) => {
      await queryClient.cancelQueries({ queryKey: ["todos"] });
      const previousTodos = queryClient.getQueriesData<TodoListResponse>({ queryKey: ["todos"] });

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
    onError: (_err, _variables, context) => {
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

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }): Promise<Todo> => {
      const response = await api.post(`/todos/${todo_id}/tags`, { tag_id });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached!");
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to attach tag";
      toast.error(msg);
    },
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }): Promise<Todo> => {
      const response = await api.delete(`/todos/${todo_id}/tags/${tag_id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag removed!");
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to remove tag";
      toast.error(msg);
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
    }): Promise<{ updated_count: number }> => {
      const response = await api.patch("/todos/bulk-status", { todo_ids, completed });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(`Updated ${data.updated_count} todos successfully!`);
    },
    onError: (err: any) => {
      const msg = err.response?.data?.detail || "Failed to bulk update status";
      toast.error(msg);
    },
  });
}
