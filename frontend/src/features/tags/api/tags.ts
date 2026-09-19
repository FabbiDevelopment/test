import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { getApiErrorMessage } from "@/lib/apiError";
import { queryClient } from "@/lib/queryClient";
import { todoKeys } from "@/features/todos/api/queryKeys";
import type { TagFormData } from "../schemas/tag";
import type { Tag } from "../types";

const TAG_QUERY_ROOT = ["tags"] as const;

export const tagKeys = {
  all: TAG_QUERY_ROOT,
  user: (userId: string) => [...TAG_QUERY_ROOT, userId] as const,
};

function invalidateTagAndTodoQueries(userId: string) {
  return Promise.all([
    queryClient.invalidateQueries({ queryKey: tagKeys.user(userId) }),
    queryClient.invalidateQueries({ queryKey: todoKeys.user(userId) }),
  ]);
}

export function useTags(userId: string | undefined) {
  return useQuery({
    queryKey: tagKeys.user(userId ?? "anonymous"),
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
    enabled: Boolean(userId),
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: TagFormData): Promise<Tag> => {
      const response = await api.post("/tags", {
        name: data.name,
        color: data.color || undefined,
      });
      return response.data;
    },
    onSuccess: async (tag) => {
      await invalidateTagAndTodoQueries(tag.user_id);
      toast.success("Tag created");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to create tag"));
    },
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TagFormData }): Promise<Tag> => {
      const response = await api.patch(`/tags/${id}`, {
        name: data.name,
        color: data.color || undefined,
      });
      return response.data;
    },
    onSuccess: async (tag) => {
      await invalidateTagAndTodoQueries(tag.user_id);
      toast.success("Tag updated");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to update tag"));
    },
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async ({ id }: { id: string; userId: string }) => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: async (_data, { userId }) => {
      await invalidateTagAndTodoQueries(userId);
      toast.success("Tag deleted");
    },
    onError: (error) => {
      toast.error(getApiErrorMessage(error, "Failed to delete tag"));
    },
  });
}
