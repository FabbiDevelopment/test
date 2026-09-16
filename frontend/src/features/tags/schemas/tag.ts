import { z } from "zod";

// THÊM: zod schema khớp backend TagCreate — Level 4 tag form validation
export const tagSchema = z.object({
  name: z.string().min(1, "Tag name is required").max(50, "Max 50 characters"),
  color: z.string().max(20).optional().or(z.literal("")),
});

export type TagFormData = z.infer<typeof tagSchema>;
