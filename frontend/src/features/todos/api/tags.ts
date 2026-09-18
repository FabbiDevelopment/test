import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { queryClient } from "@/lib/queryClient";
import type { Tag } from "./todos";

const tagsKey = ["tags"] as const;
const refresh = () => { queryClient.invalidateQueries({ queryKey: tagsKey }); queryClient.invalidateQueries({ queryKey: ["todos"] }); };
export function useTags() { return useQuery({ queryKey: tagsKey, queryFn: async (): Promise<Tag[]> => (await api.get("/tags")).data }); }
export function useCreateTag() { return useMutation({ mutationFn: async (data: { name: string; color?: string }) => (await api.post("/tags", data)).data, onSuccess: () => { refresh(); toast.success("Tag created"); }, onError: () => toast.error("Tag name already exists") }); }
export function useUpdateTag() { return useMutation({ mutationFn: async ({ id, ...data }: { id: string; name: string; color?: string }) => (await api.patch(`/tags/${id}`, data)).data, onSuccess: refresh, onError: () => toast.error("Could not rename tag") }); }
export function useDeleteTag() { return useMutation({ mutationFn: async (id: string) => api.delete(`/tags/${id}`), onSuccess: refresh, onError: () => toast.error("Could not delete tag") }); }
