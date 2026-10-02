import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import { useCurrentUser } from "@/features/auth/api/auth";

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


export function useTodos(page: number = 1, size: number = 10000) {
  const { data: user } = useCurrentUser();
  return useQuery({
    queryKey: ["todos", user?.id, page, size],
    enabled: !!user,
    queryFn: async ({ signal }): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: { page, size },
        signal,
      });
      return response.data;
    },
  });
}

export function useCreateTodo() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] });
      toast.success("Todo created successfully!");
    },
    onError: () => {
      toast.error("Failed to create todo");
    },
  });
}


export function useUpdateTodo() {
  const { data: user } = useCurrentUser();
  const queryKey = ["todos", user?.id];
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
      await queryClient.cancelQueries({ queryKey });

      // Snapshot previous value
      const previousTodos = queryClient.getQueriesData<TodoListResponse>({ queryKey });

      // Optimistically update
      queryClient.setQueriesData<TodoListResponse>({ queryKey }, (previous) => {
        if (!previous) return previous;
        return {
          ...previous,
          items: previous.items.map((todo) =>
            todo.id === id ? { ...todo, ...data } : todo
          ),
        };
      });

      return { previousTodos };
    },
    onError: () => {
      toast.error("Failed to update todo");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey });
    },
  });
}

export function useDeleteTodo() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] });
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
