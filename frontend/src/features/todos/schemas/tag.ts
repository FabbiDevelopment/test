import { z } from "zod";

export const tagSchema = z.object({
  name: z.string().trim().min(1, "Name is required").max(50, "Maximum 50 characters"),
  color: z.string().max(20, "Maximum 20 characters").optional(),
});

export type TagFormData = z.infer<typeof tagSchema>;
