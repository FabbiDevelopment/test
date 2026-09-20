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

interface CreateTagRequest {
  name: string;
  color?: string;
}

interface UpdateTagRequest {
  name?: string;
  color?: string;
}

interface BulkStatusRequest {
  todo_ids: string[];
  completed: boolean;
}

export function useTags() {
  return useQuery({
    queryKey: ["tags"],
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: CreateTagRequest): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      toast.success("Tag created successfully!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to create tag");
    },
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: UpdateTagRequest }): Promise<Tag> => {
      const response = await api.patch(`/tags/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag updated successfully!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to update tag");
    },
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["tags"] });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag deleted successfully!");
    },
    onError: () => {
      toast.error("Failed to delete tag");
    },
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }): Promise<void> => {
      await api.post(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached!");
    },
    onError: () => {
      toast.error("Failed to attach tag");
    },
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({ todoId, tagId }: { todoId: string; tagId: string }): Promise<void> => {
      await api.delete(`/todos/${todoId}/tags/${tagId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag detached!");
    },
    onError: () => {
      toast.error("Failed to detach tag");
    },
  });
}

export function useBulkStatusUpdate() {
  return useMutation({
    mutationFn: async (data: BulkStatusRequest): Promise<void> => {
      await api.patch("/todos/bulk-status", data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Bulk status updated!");
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || "Failed to bulk update status");
    },
  });
}
