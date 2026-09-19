import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/apiError";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "@/features/tags/types";
import {
  DEFAULT_TODO_PAGE_SIZE,
  normalizeTodoFilters,
  todoKeys,
  type TodoFilters,
} from "./queryKeys";
import {
  handleBulkStatusFailure,
  handleBulkStatusSuccess,
} from "./mutationHandlers";

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  // Optional while browser caches drain during a rolling deployment from the
  // pre-Tag response contract. New API responses always include this field.
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

interface UpdateTodoVariables {
  id: string;
  userId: string;
  data: UpdateTodoRequest;
}

interface DeleteTodoVariables {
  id: string;
  userId: string;
}

interface BulkStatusVariables {
  todoIds: string[];
  completed: boolean;
  userId: string;
}

interface TodoTagVariables {
  todoId: string;
  tagId: string;
  userId: string;
}

export function useTodos(
  userId: string | undefined,
  page: number = 1,
  size: number = DEFAULT_TODO_PAGE_SIZE,
  filters: TodoFilters = {},
) {
  const normalizedFilters = normalizeTodoFilters(filters);

  return useQuery({
    queryKey: todoKeys.list(userId ?? "anonymous", page, size, normalizedFilters),
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: {
          page,
          // `size` remains the documented compatible alias and preserves the
          // deployed request contract while the API also accepts `page_size`.
          size,
          ...(normalizedFilters.keyword && { keyword: normalizedFilters.keyword }),
          ...(normalizedFilters.status !== "all" && {
            status: normalizedFilters.status === "completed",
          }),
          ...(normalizedFilters.tagId && { tag_id: normalizedFilters.tagId }),
          ...(normalizedFilters.dateFrom && { date_from: normalizedFilters.dateFrom }),
          ...(normalizedFilters.dateTo && { date_to: normalizedFilters.dateTo }),
        },
      });
      return response.data;
    },
    enabled: Boolean(userId),
  });
}

export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: (todo) => {
      queryClient.invalidateQueries({ queryKey: todoKeys.user(todo.user_id) });
      toast.success("Todo created successfully!");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to create todo"));
    },
  });
}

export function useUpdateTodo() {
  return useMutation({
    mutationFn: async ({ id, data }: UpdateTodoVariables): Promise<Todo> => {
      const response = await api.put(`/todos/${id}`, data);
      return response.data;
    },
    onMutate: async ({ id, userId, data }) => {
      const queryKey = todoKeys.user(userId);
      await queryClient.cancelQueries({ queryKey });

      const previousTodos = queryClient.getQueriesData<TodoListResponse>({
        queryKey,
      });

      queryClient.setQueriesData<TodoListResponse>({ queryKey }, (todos) => {
        if (!todos) {
          return todos;
        }

        return {
          ...todos,
          items: todos.items.map((todo) =>
            todo.id === id ? { ...todo, ...data } : todo
          ),
        };
      });

      return { previousTodos };
    },
    onError: (error, _variables, context) => {
      context?.previousTodos.forEach(([queryKey, todos]) => {
        queryClient.setQueryData(queryKey, todos);
      });
      toast.error(getApiErrorMessage(error, "Failed to update todo"));
    },
    onSettled: (_data, _error, { userId }) => {
      queryClient.invalidateQueries({ queryKey: todoKeys.user(userId) });
    },
  });
}

export function useDeleteTodo() {
  return useMutation({
    mutationFn: async ({ id }: DeleteTodoVariables): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: (_data, { userId }) => {
      queryClient.invalidateQueries({ queryKey: todoKeys.user(userId) });
      toast.success("Todo deleted successfully!");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to delete todo"));
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
        userId: todo.user_id,
        data: { completed: !todo.completed },
      });
    },
  };
}

export function useAttachTodoTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: TodoTagVariables): Promise<void> => {
      await api.post(`/todos/${todoId}/tags`, { tag_id: tagId });
    },
    onSuccess: async (_data, { userId }) => {
      await queryClient.invalidateQueries({ queryKey: todoKeys.user(userId) });
      toast.success("Tag added to todo");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to add tag to todo"));
    },
  });
}

export function useDetachTodoTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: TodoTagVariables): Promise<void> => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: async (_data, { userId }) => {
      await queryClient.invalidateQueries({ queryKey: todoKeys.user(userId) });
      toast.success("Tag removed from todo");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to remove tag from todo"));
    },
  });
}

export function useBulkUpdateTodoStatus() {
  return useMutation({
    mutationFn: async ({ todoIds, completed }: BulkStatusVariables) => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids: todoIds,
        completed,
      });
      return response.data as { updated_count: number; completed: boolean };
    },
    onSuccess: async (result, { userId }) => {
      await handleBulkStatusSuccess(queryClient, toast, userId, result);
    },
    onError: (error) => {
      handleBulkStatusFailure(
        toast,
        getApiErrorMessage(error, "Failed to update selected todos"),
      );
    },
  });
}
