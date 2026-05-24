import { Router } from 'express';
import { startGrading, getGradingJobStatus, getGradingResult, reviewGradingResult } from '../controllers/gradingController';

export const gradingRouter = Router();
gradingRouter.post('/grading/start', startGrading);
gradingRouter.get('/grading/jobs/:jobId', getGradingJobStatus);
gradingRouter.get('/grading/results/:assignmentId/:studentId', getGradingResult);
gradingRouter.patch('/grading/results/:resultId/review', reviewGradingResult);