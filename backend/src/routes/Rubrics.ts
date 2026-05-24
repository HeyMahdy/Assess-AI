

import { Router } from 'express';
import { uploadRubric, getRubricsByAssignment, updateRubric } from '../controllers/rubricController';

export const rubricRouter = Router();
rubricRouter.post('/assignments/:assignmentId/rubrics/upload', uploadRubric);
rubricRouter.get('/assignments/:assignmentId/rubrics', getRubricsByAssignment);
rubricRouter.patch('/rubrics/:rubricId', updateRubric);