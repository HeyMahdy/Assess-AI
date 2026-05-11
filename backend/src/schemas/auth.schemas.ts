import { z } from 'zod';

const emailSchema = z.string().email().max(320);

export const signupBodySchema = z.object({
  email: emailSchema,
  password: z.string().min(8).max(128),
  display_name: z.string().trim().max(200).optional(),
});

export const loginBodySchema = z.object({
  email: emailSchema,
  password: z.string().min(1).max(128),
});

export const passwordForgotBodySchema = z.object({
  email: emailSchema,
});

export const passwordResetBodySchema = z.object({
  email: emailSchema,
  token: z.string().min(1).max(1024),
  newPassword: z.string().min(8).max(128),
});

export const refreshBodySchema = z.object({
  refresh_token: z.string().min(1).max(4096),
});

export type SignupBody = z.infer<typeof signupBodySchema>;
export type LoginBody = z.infer<typeof loginBodySchema>;
export type PasswordForgotBody = z.infer<typeof passwordForgotBodySchema>;
export type PasswordResetBody = z.infer<typeof passwordResetBodySchema>;
export type RefreshBody = z.infer<typeof refreshBodySchema>;
