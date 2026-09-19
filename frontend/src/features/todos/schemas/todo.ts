import { z } from "zod";

export const todoSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string(),
});

export type TodoFormData = z.infer<typeof todoSchema>;

export const todoFiltersSchema = z
  .object({
    keyword: z.string().max(200, "Keyword must be at most 200 characters"),
    status: z.enum(["all", "active", "completed"]),
    tagId: z.string(),
    dateFrom: z.string(),
    dateTo: z.string(),
  })
  .refine(
    ({ dateFrom, dateTo }) => !dateFrom || !dateTo || dateFrom <= dateTo,
    {
      message: "Start date must be before or equal to end date",
      path: ["dateTo"],
    },
  );

export type TodoFiltersFormData = z.infer<typeof todoFiltersSchema>;
