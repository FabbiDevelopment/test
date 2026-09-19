import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
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

export interface CreateTagRequest {
  name: string;
  color?: string | null;
}

export interface UpdateTagRequest {
  name?: string;
  color?: string | null;
}

// lấy danh sách tất cả Tag của User
export function useTags() {
  return useQuery<Tag[]>({
    queryKey: ["tags"],
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
  });
}

//  tạo mới Tag
export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: CreateTagRequest): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      toast.success("Tạo thẻ tag thành công!");
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || "Không thể tạo thẻ tag";
      toast.error(detail);
    },
  });
}

// cập nhật Tag
export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({
      id,
      data,
    }: {
      id: string;
      data: UpdateTagRequest;
    }): Promise<Tag> => {
      const response = await api.patch(`/tags/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Cập nhật thẻ tag thành công!");
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || "Không thể cập nhật thẻ tag";
      toast.error(detail);
    },
  });
}

// xóa Tag
export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Xóa thẻ tag thành công!");
    },
    onError: (error: any) => {
      const detail = error?.response?.data?.detail || "Không thể xóa thẻ tag";
      toast.error(detail);
    },
  });
}
