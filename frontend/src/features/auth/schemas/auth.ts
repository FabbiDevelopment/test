import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters").max(72, "Password must be at most 72 characters").refine((value) => new TextEncoder().encode(value).length <= 72, "Password must be at most 72 UTF-8 bytes"),
});

export const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: z.string().min(6, "Password must be at least 6 characters").max(72, "Password must be at most 72 characters").refine((value) => new TextEncoder().encode(value).length <= 72, "Password must be at most 72 UTF-8 bytes"),
  confirmPassword: z.string().min(6, "Password must be at least 6 characters").max(72, "Password must be at most 72 characters").refine((value) => new TextEncoder().encode(value).length <= 72, "Password must be at most 72 UTF-8 bytes"),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
