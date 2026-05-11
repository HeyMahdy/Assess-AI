import type { RequestHandler } from 'express';
import { z } from 'zod';
import { HttpError } from '../common/HttpError.js';
import {
  updateMyProfileBodySchema,
  updateUserByIdBodySchema,
  updateUserByIdParamsSchema,
} from '../schemas/user.schemas.js';
import * as userService from '../services/user.service.js';

function assertParse<T>(
  parsed: import('zod').SafeParseReturnType<unknown, T>,
): asserts parsed is import('zod').SafeParseSuccess<T> {
  if (!parsed.success) {
    const msg = parsed.error.issues.map((i) => i.message).join('; ');
    throw new HttpError(400, msg);
  }
}

const listUsersQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).optional().default(50),
  offset: z.coerce.number().int().min(0).max(500_000).optional().default(0),
});

export const getMe: RequestHandler = async (req, res, next) => {
  try {
    const token = req.authUser?.accessToken;
    if (!token) {
      throw new HttpError(401, 'Unauthorized');
    }
    const profile = await userService.getProfileByAccessToken(token);
    res.status(200).json(profile);
  } catch (err) {
    next(err);
  }
};

export const patchMe: RequestHandler = async (req, res, next) => {
  try {
    const token = req.authUser?.accessToken;
    if (!token) {
      throw new HttpError(401, 'Unauthorized');
    }
    const parsed = updateMyProfileBodySchema.safeParse(req.body);
    assertParse(parsed);
    const profile = await userService.updateMyProfile(token, parsed.data);
    res.status(200).json(profile);
  } catch (err) {
    next(err);
  }
};

export const listUsers: RequestHandler = async (_req, res, next) => {
  try {
    const parsed = listUsersQuerySchema.safeParse({
      limit: _req.query['limit'],
      offset: _req.query['offset'],
    });
    assertParse(parsed);
    const page = await userService.listUsersAsAdmin(parsed.data);
    res.status(200).json(page);
  } catch (err) {
    next(err);
  }
};

export const patchUserById: RequestHandler = async (req, res, next) => {
  try {
    const parsedParams = updateUserByIdParamsSchema.safeParse({ userId: req.params['userId'] });
    assertParse(parsedParams);
    const parsedBody = updateUserByIdBodySchema.safeParse(req.body);
    assertParse(parsedBody);
    const profile = await userService.updateUserAsAdmin(parsedParams.data.userId, parsedBody.data);
    res.status(200).json(profile);
  } catch (err) {
    next(err);
  }
};
