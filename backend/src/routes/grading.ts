import { Router } from 'express';
import { startGrading, getGradingResults } from '../controllers/gradingController.js';
import { requireAccessToken } from '../common/middleware/jwt.middleware.js';

export const gradingRouter = Router();

gradingRouter.use(requireAccessToken);

// Trigger grading for a student's assignment
gradingRouter.post('/assignments/:assignmentId/students/:studentId/grade', startGrading);

// Get grading results for a student on an assignment
gradingRouter.get('/assignments/:assignmentId/students/:studentId/scores', getGradingResults);
