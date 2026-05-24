import { Router } from 'express';
import { getAssignmentAnalytics, getAssignmentMistakes, getStudentProgress } from '../controllers/analyticsController';

export const analyticsRouter = Router();
analyticsRouter.get('/analytics/assignments/:assignmentId', getAssignmentAnalytics);
analyticsRouter.get('/analytics/assignments/:assignmentId/mistakes', getAssignmentMistakes);
analyticsRouter.get('/analytics/students/:studentId/progress', getStudentProgress);