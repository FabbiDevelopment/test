import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "../../tags/api/tags";

export type { Tag };

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  user_email?: string | null;
  created_at: string;
  updated_at: string;
  tags?: Tag[];
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
  status?: string;
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
}

export function useTodos(filters: TodoFilters = {}) {
  return useQuery({
    queryKey: ["todos", filters],
    queryFn: async (): Promise<TodoListResponse> => {
      const params: Record<string, string | number> = {};
      if (filters.page) params.page = filters.page;
      if (filters.size) params.size = filters.size;
      if (filters.status !== undefined && filters.status !== "") params.status = filters.status;
      if (filters.tag_id) params.tag_id = filters.tag_id;
      if (filters.keyword) params.keyword = filters.keyword;
      if (filters.date_from) params.date_from = filters.date_from;
      if (filters.date_to) params.date_to = filters.date_to;
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

      // Snapshot all matching todo queries
      const previousSnapshots = queryClient.getQueriesData<TodoListResponse>({ queryKey: ["todos"] });

      // Optimistically update all matching queries
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

      return { previousSnapshots };
    },
    onError: (_err, _variables, context) => {
      context?.previousSnapshots?.forEach(([queryKey, data]) => {
        queryClient.setQueryData(queryKey, data);
      });
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

export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async (data: { todo_ids: string[]; completed: boolean }) => {
      const response = await api.patch("/todos/bulk-status", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Todos updated successfully!");
    },
    onError: () => { toast.error("Failed to update todos"); },
  });
}
