import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

import { Tag } from "@/features/tags/api/tags";

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

export interface TodoFilterParams {
  keyword?: string;
  status?: string;
  tagId?: string;
  dateFrom?: string;
  dateTo?: string;
}

export function useTodos(
  page: number = 1,
  size: number = 20,
  filterParams?: TodoFilterParams
) {
  const queryParams: Record<string, any> = { page, size };

  if (filterParams?.keyword) queryParams.keyword = filterParams.keyword;
  if (filterParams?.status && filterParams.status !== "all") queryParams.status = filterParams.status;
  if (filterParams?.tagId && filterParams.tagId !== "all") queryParams.tag_id = filterParams.tagId;
  if (filterParams?.dateFrom) queryParams.date_from = filterParams.dateFrom;
  if (filterParams?.dateTo) queryParams.date_to = filterParams.dateTo;

  return useQuery({
    queryKey: ["todos", page, size, filterParams],
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: queryParams,
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
    onError: () => {
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
