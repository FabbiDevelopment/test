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

interface TagMutationInput {
  name: string;
  color?: string | null;
}

export const tagsQueryKey = ["tags"] as const;

export function useTags() {
  return useQuery({
    queryKey: tagsQueryKey,
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: TagMutationInput): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagsQueryKey });
      toast.success("Tag created");
    },
    onError: (error: unknown) => {
      const message = isConflict(error)
        ? "You already have a tag with this name"
        : "Failed to create tag";
      toast.error(message);
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
      data: Partial<TagMutationInput>;
    }): Promise<Tag> => {
      const response = await api.patch(`/tags/${id}`, data);
      return response.data;
    },
    onSuccess: () => {
      // Tags are embedded in each todo's response, so a rename must also
      // refresh whatever todo lists are cached, not just the tag list.
      queryClient.invalidateQueries({ queryKey: tagsQueryKey });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag updated");
    },
    onError: (error: unknown) => {
      const message = isConflict(error)
        ? "You already have a tag with this name"
        : "Failed to update tag";
      toast.error(message);
    },
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string): Promise<void> => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: tagsQueryKey });
      queryClient.invalidateQueries({ queryKey: ["todos"] });
      toast.success("Tag deleted");
    },
    onError: () => {
      toast.error("Failed to delete tag");
    },
  });
}

export function useAttachTag() {
  return useMutation({
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }) => {
      const response = await api.post(`/todos/${todoId}/tags`, { tag_id: tagId });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
    onError: () => {
      toast.error("Failed to attach tag");
    },
  });
}

export function useDetachTag() {
  return useMutation({
    mutationFn: async ({
      todoId,
      tagId,
    }: {
      todoId: string;
      tagId: string;
    }) => {
      const response = await api.delete(`/todos/${todoId}/tags/${tagId}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["todos"] });
    },
    onError: () => {
      toast.error("Failed to detach tag");
    },
  });
}

function isConflict(error: unknown): boolean {
  return (
    typeof error === "object" &&
    error !== null &&
    "response" in error &&
    (error as { response?: { status?: number } }).response?.status === 409
  );
}
