import { z } from "zod";
export const tagSchema = z.object({
  name: z.string().min(1, "Tag name is required").max(50, "Tag name is too long"),
  color: z.string().max(20).optional(),
});
export type TagFormData = z.infer<typeof tagSchema>;
