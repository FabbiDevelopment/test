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

export interface TagInput {
  name: string;
  color?: string | null;
}

export const tagKeys = { all: ["tags"] as const };

async function invalidateTagData() {
  await Promise.all([
    queryClient.invalidateQueries({ queryKey: tagKeys.all }),
    queryClient.invalidateQueries({ queryKey: ["todos"] }),
  ]);
}

export function useTags() {
  return useQuery({
    queryKey: tagKeys.all,
    queryFn: async (): Promise<Tag[]> => {
      const response = await api.get("/tags");
      return response.data;
    },
  });
}

export function useCreateTag() {
  return useMutation({
    mutationFn: async (data: TagInput): Promise<Tag> => {
      const response = await api.post("/tags", data);
      return response.data;
    },
    onSuccess: async () => {
      await invalidateTagData();
      toast.success("Tag created");
    },
    onError: () => toast.error("Could not create tag"),
  });
}

export function useUpdateTag() {
  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TagInput }) => {
      const response = await api.patch(`/tags/${id}`, data);
      return response.data as Tag;
    },
    onSuccess: async () => {
      await invalidateTagData();
      toast.success("Tag updated");
    },
    onError: () => toast.error("Could not update tag"),
  });
}

export function useDeleteTag() {
  return useMutation({
    mutationFn: async (id: string) => {
      await api.delete(`/tags/${id}`);
    },
    onSuccess: async () => {
      await invalidateTagData();
      toast.success("Tag deleted");
    },
    onError: () => toast.error("Could not delete tag"),
  });
}
