import { z } from "zod";

export const todoSchema = z.object({
  title: z.string().min(1, "Title is required").max(200, "Title is too long"),
  description: z.string().optional(),
});

export type TodoFormData = z.infer<typeof todoSchema>;

export const tagSchema = z.object({
  name: z.string().trim().min(1, "Tag name is required").max(50),
  color: z.string().regex(/^#[0-9a-fA-F]{6}$/, "Choose a valid color"),
});

export type TagFormData = z.infer<typeof tagSchema>;
