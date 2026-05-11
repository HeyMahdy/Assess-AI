import { z } from 'zod';
import { USER_ROLES } from '../types/roles.js';

const uuidSchema = z.string().uuid();

export const updateMyProfileBodySchema = z
  .object({
    display_name: z.string().trim().max(200).nullable().optional(),
    avatar_url: z.string().url().max(2048).nullable().optional(),
  })
  .strict();

export const updateUserByIdParamsSchema = z.object({
  userId: uuidSchema,
});

export const updateUserByIdBodySchema = z
  .object({
    display_name: z.string().trim().max(200).nullable().optional(),
    avatar_url: z.string().url().max(2048).nullable().optional(),
    role: z.enum(USER_ROLES).optional(),
  })
  .strict()
  .refine((v) => Object.keys(v).length > 0, { message: 'At least one field is required' });

export type UpdateMyProfileBody = z.infer<typeof updateMyProfileBodySchema>;
export type UpdateUserByIdParams = z.infer<typeof updateUserByIdParamsSchema>;
export type UpdateUserByIdBody = z.infer<typeof updateUserByIdBodySchema>;
