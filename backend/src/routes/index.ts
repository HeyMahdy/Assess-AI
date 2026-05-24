import { Router } from 'express';
import { authRouter } from './authRoute.js';
import { healthRouter } from './healthRoute.js';
import { userRouter } from './userRoute.js';
import { assignmentRouter } from './Assignment.js';
import {questionRouter} from './Question.js'

export const rootRouter = Router();

rootRouter.use(healthRouter);
rootRouter.use('/auth', authRouter);
rootRouter.use('/users', userRouter);
rootRouter.use('/assignments', assignmentRouter);
rootRouter.use('/teachers', assignmentRouter);
rootRouter.use('/',questionRouter)
