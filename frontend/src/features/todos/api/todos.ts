import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "@/features/tags/api/tagsApi";

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
  status?: string;
  tag_id?: string;
  keyword?: string;
  date_from?: string;
  date_to?: string;
  page?: number;
  size?: number;
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

export interface BulkStatusRequest {
  todo_ids: string[];
  completed: boolean;
}

// lấy danh sách công và phân trang
export function useTodos(params: TodoFilterParams = {}) {
  const { status, tag_id, keyword, date_from, date_to, page = 1, size = 50 } = params;

  return useQuery<TodoListResponse>({
    queryKey: ["todos", { status, tag_id, keyword, date_from, date_to, page, size }],
    queryFn: async (): Promise<TodoListResponse> => {
      const response = await api.get("/todos", {
        params: {
          status: status || undefined,
          tag_id: tag_id || undefined,
          keyword: keyword || undefined,
          date_from: date_from || undefined,
          date_to: date_to || undefined,
          page,
          size,
        },
      });
      return response.data;
    },
  });
}

// tạo Todo
export function useCreateTodo() {
  return useMutation({
    mutationFn: async (data: CreateTodoRequest): Promise<Todo> => {
      const response = await api.post("/todos", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tạo công việc thành công!");
    },
    onError: () => {
      toast.error("Không thể tạo công việc");
    },
  });
}

//  cập nhật  
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
      const previousTodos = queryClient.getQueryData<TodoListResponse>(["todos"]);

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
      toast.error("Không thể cập nhật công việc");
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
  });
}

// xóa 
export function useDeleteTodo() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/todos/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Đã xóa công việc!");
    },
    onError: () => {
      toast.error("Không thể xóa công việc");
    },
  });
}

// chuyển đổi nhanh trạng thái hoàn thành
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

// cập nhật trạng thái hàng loạt (Bulk Status Update)
export function useBulkUpdateStatus() {
  return useMutation({
    mutationFn: async (payload: BulkStatusRequest): Promise<{ updated_count: number }> => {
      const response = await api.patch("/todos/bulk-status", payload);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success(`Đã cập nhật ${data.updated_count} công việc!`);
    },
    onError: () => {
      toast.error("Thao tác hàng loạt thất bại!");
    },
  });
}

// gán Tag 
export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }): Promise<Todo> => {
      const response = await api.post(`/todos/${todoId}/tags`, { tag_id: tagId });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Đã gắn thẻ tag!");
    },
    onError: () => {
      toast.error("Không thể gắn thẻ tag");
    },
  });
}

//  gỡ Tag
export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }): Promise<Todo> => {
      const response = await api.delete(`/todos/${todoId}/tags/${tagId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Đã gỡ thẻ tag!");
    },
    onError: () => {
      toast.error("Không thể gỡ thẻ tag");
    },
  });
}
