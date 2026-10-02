import { z } from "zod";

export const todoSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().optional(),
});

export type TodoFormData = z.infer<typeof todoSchema>;

export const todoFiltersSchema = z
  .object({
    keyword: z.string().max(200, "Keyword must be 200 characters or fewer"),
    status: z.enum(["all", "active", "completed"]),
    tagId: z.string(),
    dateFrom: z.string(),
    dateTo: z.string(),
  })
  .refine(
    ({ dateFrom, dateTo }) => !dateFrom || !dateTo || dateFrom <= dateTo,
    {
      message: "Start date must be on or before end date",
      path: ["dateTo"],
    }
  );

export type TodoFiltersFormData = z.infer<typeof todoFiltersSchema>;

export const tagSchema = z.object({
  name: z.string().trim().min(1, "Tag name is required").max(50),
  color: z.string().trim().max(20, "Color must be 20 characters or fewer"),
});

export type TagFormData = z.infer<typeof tagSchema>;
