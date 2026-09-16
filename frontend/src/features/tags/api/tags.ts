import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";

export interface Tag {
  id: string;
  name: string;
  color: string | null;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface CreateTagRequest {
  name: string;
  color?: string;
}

export interface UpdateTagRequest {
  name?: string;
  color?: string;
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
      const msg = error?.response?.data?.detail || "Failed to create tag";
      toast.error(msg);
    },
  });
}

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
      toast.success("Tag updated successfully!");
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || "Failed to update tag";
      toast.error(msg);
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
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || "Failed to delete tag";
      toast.error(msg);
    },
  });
}

export function useAttachTagToTodo() {
  return useMutation({
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }): Promise<void> => {
      await api.post(`/todos/${todoId}/tags`, { tag_id: tagId });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag attached!");
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || "Failed to attach tag";
      toast.error(msg);
    },
  });
}

export function useDetachTagFromTodo() {
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
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag detached!");
    },
    onError: (error: any) => {
      const msg = error?.response?.data?.detail || "Failed to detach tag";
      toast.error(msg);
    },
  });
}
