import type { RequestHandler } from 'express';
import { HttpError } from '../HttpError.js';
import type { UserRoleName } from '../../types/roles.js';

export function requireRoles(...allowed: UserRoleName[]): RequestHandler {
  return (req, _res, next) => {
    const role = req.profile?.role;
    if (!role || !allowed.includes(role)) {
      next(new HttpError(403, 'Forbidden'));
      return;
    }
    next();
  };
}
