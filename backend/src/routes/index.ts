import { Router } from 'express';
import { healthRouter } from './healthRoute.js';

export const rootRouter = Router();

rootRouter.use(healthRouter);
