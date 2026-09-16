import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface TagBrief {
  id: string;
  name: string;
  color: string | null;
}

export interface Todo {
  id: string;
  title: string;
  description: string | null;
  completed: boolean;
  user_id: string;
  created_at: string;
  updated_at: string;
  tags?: TagBrief[]; // THÊM: tags từ backend Level 4
}

export interface TodoFilters {
  page?: number;
  size?: number;
  status?: "" | "active" | "completed";
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
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

// THÊM: queryKey phải gồm mọi filter param — Level 4 requirement
function todosQueryKey(filters: TodoFilters) {
  return [
    "todos",
    filters.page ?? 1,
    filters.size ?? 10000,
    filters.status ?? "",
    filters.tag_id ?? "",
    filters.keyword ?? "",
    filters.date_from ?? "",
    filters.date_to ?? "",
  ] as const;
}

export function useTodos(filters: TodoFilters = {}) {
  const page = filters.page ?? 1;
  const size = filters.size ?? 10000;

  return useQuery({
    // SAI: queryKey: ["todos"] — bỏ qua page/size/filters, React Query tái sử dụng cache sai
    // Không xóa comment SAI; dùng key đầy đủ bên dưới
    // queryKey: ["todos"],
    queryKey: todosQueryKey(filters), // THÊM: cache identity theo toàn bộ filter params
    queryFn: async (): Promise<TodoListResponse> => {
      const params: Record<string, string | number> = { page, size };
      if (filters.status) params.status = filters.status;
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
      await queryClient.cancelQueries({ queryKey: ["todos"] });

      // SAI: getQueryData(["todos"]) — key thiếu filters nên không khớp cache thực tế
      // THÊM: snapshot tất cả query prefix ["todos"] để rollback đúng
      const previousQueries = queryClient.getQueriesData<TodoListResponse>({
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

      return { previousQueries };
    },
    // SAI: onError chỉ toast, không rollback → UI sai sau lỗi API
    // THÊM: khôi phục snapshot trước mutate
    onError: (_err, _vars, context) => {
      if (context?.previousQueries) {
        for (const [queryKey, data] of context.previousQueries) {
          queryClient.setQueryData(queryKey, data);
        }
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

// THÊM: bulk status update — Level 4 PATCH /todos/bulk-status
export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async ({
      todoIds,
      completed,
    }: {
      todoIds: string[];
      completed: boolean;
    }) => {
      const response = await api.patch("/todos/bulk-status", {
        todo_ids: todoIds,
        completed,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Bulk update completed!");
    },
    onError: () => {
      toast.error("Bulk update failed");
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
