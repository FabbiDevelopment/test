import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { getAuthSessionKey } from "@/features/auth/api/session";

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
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

const todoKeys = {
  all: ["todos"] as const,
  list: (page: number, size: number, sessionKey: string | null) =>
    [...todoKeys.all, "list", { page, size, sessionKey }] as const,
};

export function useTodos(page: number = 1, size: number = 50) {
  const sessionKey = getAuthSessionKey();

  return useQuery({
    queryKey: todoKeys.list(page, size, sessionKey),
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: { page, size },
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
      queryClient.invalidateQueries({ queryKey: todoKeys.all });
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
      await queryClient.cancelQueries({ queryKey: todoKeys.all });

      // Snapshot previous value
      const previousTodos = queryClient.getQueriesData<TodoListResponse>({
        queryKey: todoKeys.all,
      });

      // Optimistically update
      previousTodos.forEach(([queryKey, todos]) => {
        if (!todos) {
          return;
        }

        queryClient.setQueryData<TodoListResponse>(queryKey, {
          ...todos,
          items: todos.items.map((todo) =>
            todo.id === id ? { ...todo, ...data } : todo
          ),
        });
      });

      return { previousTodos };
    },
    onError: (_error, _variables, context) => {
      context?.previousTodos.forEach(([queryKey, todos]) => {
        queryClient.setQueryData(queryKey, todos);
      });
      toast.error("Failed to update todo");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: todoKeys.all });
    },
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: todoKeys.all });
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
