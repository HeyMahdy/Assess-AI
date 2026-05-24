import { Router } from 'express';
import { uploadSolution, getSolutionsByAssignment } from '../controllers/solutionController';

export const solutionRouter = Router();
solutionRouter.post('/assignments/:assignmentId/solutions/upload', uploadSolution);
solutionRouter.get('/assignments/:assignmentId/solutions', getSolutionsByAssignment);