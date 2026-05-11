import type { AuthUser, ProfileContext } from './auth.js';

declare global {
  namespace Express {
    interface Request {
      authUser?: AuthUser | undefined;
      profile?: ProfileContext | undefined;
    }
  }
}

export {};
