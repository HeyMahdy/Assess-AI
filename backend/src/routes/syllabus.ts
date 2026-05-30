import { Router } from 'express';
import multer from 'multer';
import { uploadSyllabus, getSyllabusGraph, getSyllabusStatus, querySyllabus, getPrerequisites } from '../controllers/syllabusController.js';
import { requireAccessToken } from '../common/middleware/jwt.middleware.js';

const upload = multer({ storage: multer.memoryStorage() });
export const syllabusRouter = Router();

syllabusRouter.use(requireAccessToken);

// Upload syllabus and trigger GraphRAG pipeline
syllabusRouter.post('/syllabus/upload', upload.single('file'), uploadSyllabus);

// Get syllabus ingestion status
syllabusRouter.get('/syllabus/:syllabusId/status', getSyllabusStatus);

// Get full graph for a syllabus (by syllabusId or assignmentId query param)
syllabusRouter.get('/syllabus/graph', getSyllabusGraph);

// Query the GraphRAG system
syllabusRouter.post('/syllabus/query', querySyllabus);

// Get prerequisite chain for a topic
syllabusRouter.get('/syllabus/:syllabusId/prerequisites/:topic', getPrerequisites);
