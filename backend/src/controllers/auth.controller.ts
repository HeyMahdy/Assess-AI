import type { RequestHandler } from 'express';
import { HttpError } from '../common/HttpError.js';
import {
  loginBodySchema,
  passwordForgotBodySchema,
  passwordResetBodySchema,
  refreshBodySchema,
  signupBodySchema,
} from '../schemas/auth.schemas.js';
import * as authService from '../services/auth.service.js';

function assertParse<T>(
  parsed: import('zod').SafeParseReturnType<unknown, T>,
): asserts parsed is import('zod').SafeParseSuccess<T> {
  if (!parsed.success) {
    const msg = parsed.error.issues.map((i) => i.message).join('; ');
    throw new HttpError(400, msg);
  }
}

export const signup: RequestHandler = async (req, res, next) => {
  try {
    const parsed = signupBodySchema.safeParse(req.body);
    assertParse(parsed);
    const result = await authService.signup(parsed.data);
    res.status(201).json(result);
  } catch (err) {
    next(err);
  }
};

export const login: RequestHandler = async (req, res, next) => {
  try {
    const parsed = loginBodySchema.safeParse(req.body);
    assertParse(parsed);
    const session = await authService.login(parsed.data);
    res.status(200).json(session);
  } catch (err) {
    next(err);
  }
};

export const passwordForgot: RequestHandler = async (req, res, next) => {
  try {
    const parsed = passwordForgotBodySchema.safeParse(req.body);
    assertParse(parsed);
    await authService.requestPasswordReset(parsed.data);
    res.status(200).json({ ok: true });
  } catch (err) {
    next(err);
  }
};

export const passwordReset: RequestHandler = async (req, res, next) => {
  try {
    const parsed = passwordResetBodySchema.safeParse(req.body);
    assertParse(parsed);
    const session = await authService.completePasswordReset(parsed.data);
    res.status(200).json(session);
  } catch (err) {
    next(err);
  }
};

export const refresh: RequestHandler = async (req, res, next) => {
  try {
    const parsed = refreshBodySchema.safeParse(req.body);
    assertParse(parsed);
    const session = await authService.refreshSession(parsed.data);
    res.status(200).json(session);
  } catch (err) {
    next(err);
  }
};
