import { Router } from 'express';
import { requireAccessToken, requireProfile } from '../common/middleware/jwt.middleware.js';
import { requireRoles } from '../common/middleware/roles.guard.middleware.js';
import * as user from '../controllers/user.controller.js';

export const userRouter = Router();

userRouter.get('/me', requireAccessToken, user.getMe);
userRouter.patch('/me', requireAccessToken, user.patchMe);
userRouter.get('/', requireAccessToken, requireProfile, requireRoles('admin'), user.listUsers);
userRouter.patch(
  '/:userId',
  requireAccessToken,
  requireProfile,
  requireRoles('admin'),
  user.patchUserById,
);
