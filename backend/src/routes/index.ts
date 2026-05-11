import { Router } from 'express';
import { authRouter } from './authRoute.js';
import { healthRouter } from './healthRoute.js';
import { userRouter } from './userRoute.js';

export const rootRouter = Router();

rootRouter.use(healthRouter);
rootRouter.use('/auth', authRouter);
rootRouter.use('/users', userRouter);
