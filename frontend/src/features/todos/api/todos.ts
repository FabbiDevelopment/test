import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "./tags";

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


export interface TodoFilters {
  page?: number;
  size?: number;
  status?: boolean | null;
  tag_id?: string | null;
  keyword?: string | null;
  date_from?: string | null;
  date_to?: string | null;
}

export function useTodos(filters: TodoFilters = {}) {
  const { page = 1, size = 10000, status, tag_id, keyword, date_from, date_to } = filters;

  return useQuery({
    queryKey: ["todos", { page, size, status, tag_id, keyword, date_from, date_to }],
    queryFn: async (): Promise<TodoListResponse> => {
      const params: Record<string, any> = { page, size };
      if (status !== undefined && status !== null) params.status = status;
      if (tag_id) params.tag_id = tag_id;
      if (keyword) params.keyword = keyword;
      if (date_from) params.date_from = date_from;
      if (date_to) params.date_to = date_to;

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
      // Cancel outgoing queries
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // Snapshot previous value
      const previousTodos = queryClient.getQueryData<TodoListResponse>(["todos"]);

      // Optimistically update
      if (previousTodos) {
        queryClient.setQueryData<TodoListResponse>(["todos"], {
          ...previousTodos,
          items: previousTodos.items.map((todo) =>
            todo.id === id ? { ...todo, ...data } : todo
          ),
        });
      }

      return { previousTodos };
    },
    onError: (_err, _variables, context) => {
      if (context?.previousTodos) {
        queryClient.setQueryData(["todos"], context.previousTodos);
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

export function useBulkUpdateTodoStatus() {
  return useMutation({
    mutationFn: async ({ todo_ids, completed }: { todo_ids: string[], completed: boolean }) => {
      await api.patch("/todos/bulk-status", { todo_ids, completed });
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

export function useAttachTagToTodo() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }): Promise<Todo> => {
      const response = await api.post(`/todos/${todo_id}/tags`, { tag_id });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached successfully!");
    },
    onError: () => {
      toast.error("Failed to attach tag");
    },
  });
}

export function useDetachTagFromTodo() {
  return useMutation({
    mutationFn: async ({ todo_id, tag_id }: { todo_id: string; tag_id: string }): Promise<Todo> => {
      const response = await api.delete(`/todos/${todo_id}/tags/${tag_id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag detached successfully!");
    },
    onError: () => {
      toast.error("Failed to detach tag");
    },
  });
}
