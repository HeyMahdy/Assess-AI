import type { Request, RequestHandler } from 'express';
import { HttpError } from '../HttpError.js';
import { createAnonClient } from '../../lib/supabase.js';
import { getProfileByAccessToken } from '../../services/user.service.js';

function readBearerToken(req: Request): string | undefined {
  const header = req.headers.authorization;
  if (typeof header !== 'string') {
    return undefined;
  }
  const trimmed = header.trim();
  if (!trimmed.toLowerCase().startsWith('bearer ')) {
    return undefined;
  }
  const token = trimmed.slice(7).trim();
  return token.length > 0 ? token : undefined;
}

export const requireAccessToken: RequestHandler = async (req, _res, next) => {
  try {
    const token = readBearerToken(req);
    if (!token) {
      next(new HttpError(401, 'Missing bearer token'));
      return;
    }
    const supabase = createAnonClient();
    const {
      data: { user },
      error,
    } = await supabase.auth.getUser(token);
    if (error || !user) {
      next(new HttpError(401, error?.message ?? 'Invalid or expired token'));
      return;
    }
    req.authUser = {
      id: user.id,
      email: user.email ?? undefined,
      accessToken: token,
    };
    next();
  } catch (err) {
    next(err);
  }
};

export const requireProfile: RequestHandler = async (req, _res, next) => {
  try {
    const token = req.authUser?.accessToken;
    if (!token) {
      next(new HttpError(401, 'Unauthorized'));
      return;
    }
    const profile = await getProfileByAccessToken(token);
    req.profile = profile;
    next();
  } catch (err) {
    next(err);
  }
};
