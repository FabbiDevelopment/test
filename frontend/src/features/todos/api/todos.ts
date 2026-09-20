import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "@/features/tags/types/tag";

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
  status?: boolean;
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
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

export function useTodos(params: TodoFilterParams = { page: 1, size: 20 }) {
  const { page = 1, size = 20, status, tag_id, keyword, date_from, date_to } = params;

  return useQuery({
    queryKey: ["todos", { page, size, status, tag_id, keyword, date_from, date_to }],
    queryFn: async (): Promise<TodoListResponse> => {
      const queryParams: Record<string, any> = { page, size };
      if (status !== undefined) queryParams.status = status;
      if (tag_id) queryParams.tag_id = tag_id;
      if (keyword && keyword.trim()) queryParams.keyword = keyword.trim();
      if (date_from) queryParams.date_from = date_from;
      if (date_to) queryParams.date_to = date_to;

      const response = await api.get("/todos", { params: queryParams });
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
  return useMutation<
    Todo,
    Error,
    { id: string; data: UpdateTodoRequest },
    { previousTodos?: [readonly unknown[], TodoListResponse | undefined][] }
  >({
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
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }): Promise<Todo> => {
      const response = await api.post(`/todos/${todoId}/tags`, {
        tag_id: tagId,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached!");
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || "Failed to attach tag";
      toast.error(message);
    },
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }): Promise<void> => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag removed!");
    },
    onError: (error: any) => {
      const message = error?.response?.data?.detail || "Failed to remove tag";
      toast.error(message);
    },
  });
}

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async ({
      todoIds,
      completed,
    }: {
      todoIds: string[];
      completed: boolean;
    }): Promise<{ updated_count: number; completed: boolean }> => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids: todoIds,
        completed,
      });
      return response.data;
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(
        `Marked ${variables.todoIds.length} todos as ${variables.completed ? "completed" : "active"
        }!`
      );
    },
    onError: () => {
      toast.error("Failed to perform bulk update");
    },
  });
}

export function useBulkDeleteTodos() {
  return useMutation({
    mutationFn: async ({
      todoIds,
    }: {
      todoIds: string[];
    }): Promise<{ deleted_count: number }> => {
      const response = await api.post("/todos/bulk-delete", {
        todo_ids: todoIds,
      });
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(
        `Deleted ${data.deleted_count} ${data.deleted_count === 1 ? "todo" : "todos"
        } successfully!`
      );
    },
    onError: () => {
      toast.error("Failed to delete todos");
    },
  });
}

