import { z } from "zod";

export const passwordSchema = z
  .string()
  .refine(
    (password) => Array.from(password).length >= 6,
    "Password must be at least 6 characters",
  )
  .refine(
    (password) => new TextEncoder().encode(password).length <= 72,
    "Password must not exceed 72 UTF-8 bytes",
  );

export const loginSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: passwordSchema,
});

export const registerSchema = z.object({
  email: z.string().email("Invalid email address"),
  password: passwordSchema,
  confirmPassword: passwordSchema,
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

export type LoginFormData = z.infer<typeof loginSchema>;
export type RegisterFormData = z.infer<typeof registerSchema>;
