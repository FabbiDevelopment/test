import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { useCurrentUser } from "@/features/auth/api/auth";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string;
  user_id: string;
  name: string;
  color: string | null;
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
  tags: Tag[];
}

interface TodoListResponse {
  items: Todo[];
  total: number;
  page: number;
  size: number;
}

interface TagListResponse {
  items: Tag[];
}

export type TodoStatus = "all" | "active" | "completed";

export interface TodoFilters {
  keyword?: string;
  status?: TodoStatus;
  tagId?: string;
  dateFrom?: string;
  dateTo?: string;
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

interface TagRequest {
  name: string;
  color: string | null;
}

export interface TodoQueryParams {
  page: number;
  page_size: number;
  keyword: string | undefined;
  status: TodoStatus;
  tag_id: string | undefined;
  date_from: string | undefined;
  date_to: string | undefined;
}

export function useTodos(filters: TodoFilters = {}) {
  const { data: user } = useCurrentUser();
  const params: TodoQueryParams = {
    page: 1,
    page_size: 10_000,
    keyword: filters.keyword?.trim() || undefined,
    status: filters.status ?? "all",
    tag_id: filters.tagId || undefined,
    date_from: filters.dateFrom || undefined,
    date_to: filters.dateTo || undefined,
  };

  return useQuery({
    queryKey: ["todos", user?.id, params],
    enabled: !!user,
    queryFn: async ({ signal }): Promise<TodoListResponse> => {
      const response = await api.get("/todos", { params, signal });
      return response.data;
    },
  });
}

export function useTags() {
  const { data: user } = useCurrentUser();
  return useQuery({
    queryKey: ["tags", user?.id],
    enabled: !!user,
    queryFn: async ({ signal }): Promise<Tag[]> => {
      const response = await api.get<TagListResponse>("/tags", { signal });
      return response.data.items;
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
    onError: () => toast.error("Failed to create todo"),
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
      await queryClient.cancelQueries({ queryKey });
      queryClient.setQueriesData<TodoListResponse>({ queryKey }, (previous) => {
        if (!previous) return previous;
        return {
          ...previous,
          items: previous.items.map((todo) =>
            todo.id === id ? { ...todo, ...data } : todo
          ),
        };
      });
    },
    onError: () => toast.error("Failed to update todo"),
    onSettled: () => queryClient.invalidateQueries({ queryKey }),
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
    onError: () => toast.error("Failed to delete todo"),
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

export function useCreateTag() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async (data: TagRequest): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", user?.id] });
      toast.success("Tag created successfully.");
    },
    onError: () => toast.error("Failed to create tag."),
  });
}

export function useUpdateTag() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: TagRequest;
    }): Promise<Tag> => {
      const response = await api.patch(`/tags/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", user?.id] });
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] });
      toast.success("Tag updated successfully.");
    },
    onError: () => toast.error("Failed to update tag."),
  });
}

export function useDeleteTag() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags", user?.id] });
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] });
      toast.success("Tag deleted successfully.");
    },
    onError: () => toast.error("Failed to delete tag."),
  });
}

export function useAttachTag() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }): Promise<Tag> => {
      const response = await api.post(`/todos/${todoId}/tags`, {
        tag_id: tagId,
      });
      return response.data;
    },
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] }),
    onError: () => toast.error("Failed to add tag to todo."),
  });
}

export function useDetachTag() {
  const { data: user } = useCurrentUser();
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
    onSuccess: () =>
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] }),
    onError: () => toast.error("Failed to remove tag from todo."),
  });
}

export function useBulkUpdateTodoStatus() {
  const { data: user } = useCurrentUser();
  return useMutation({
    mutationFn: async (data: {
      todo_ids: string[];
      completed: boolean;
    }): Promise<{ updated: number }> => {
      const response = await api.patch("/todos/bulk-status", data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["todos", user?.id] });
      toast.success(`${data.updated} todos updated.`);
    },
    onError: () => toast.error("Failed to update selected todos."),
  });
}
