import { Router } from 'express';
import { generateRemediation, getStudentFeedback, getStudentWeakConcepts } from '../controllers/remediationController';

export const remediationRouter = Router();
remediationRouter.post('/remediation/generate', generateRemediation);
remediationRouter.get('/students/:studentId/feedback', getStudentFeedback);
remediationRouter.get('/students/:studentId/weak-concepts', getStudentWeakConcepts);