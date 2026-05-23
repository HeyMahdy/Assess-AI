import { Router } from 'express';
import { 
  createAssignment, 
  getAssignmentById, 
  updateAssignment
  ,deleteAssignment
} from '../controllers/assignmentController.js'; // Adjust the import path as needed
import { requireAccessToken } from '../common/middleware/jwt.middleware.js';

export const assignmentRouter = Router();

assignmentRouter.use(requireAccessToken);

// POST /assignments
assignmentRouter.post('/', createAssignment);

// GET /assignments/:assignmentId
assignmentRouter.get('/:assignmentId', getAssignmentById);

// PATCH /assignments/:assignmentId
assignmentRouter.patch('/:assignmentId', updateAssignment);

assignmentRouter.delete('/:assignmentId',deleteAssignment)