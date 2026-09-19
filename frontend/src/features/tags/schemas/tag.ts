import { z } from "zod";

export const tagSchema = z.object({
  name: z
    .string()
    .trim()
    .min(1, "Tag name is required")
    .max(50, "Tag name must be at most 50 characters"),
  color: z.string().max(20, "Color must be at most 20 characters").optional(),
});

export type TagFormData = z.infer<typeof tagSchema>;
