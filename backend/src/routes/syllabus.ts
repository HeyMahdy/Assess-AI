import { Router } from 'express';
import multer from 'multer';
import { uploadSyllabus, getSyllabusGraph, querySyllabus, getPrerequisites } from '../controllers/syllabusController.js';
import { requireAccessToken } from '../common/middleware/jwt.middleware.js';

const upload = multer({ storage: multer.memoryStorage() });
export const syllabusRouter = Router();

syllabusRouter.use(requireAccessToken);

// Upload syllabus and trigger GraphRAG pipeline
syllabusRouter.post('/syllabus/upload', upload.single('file'), uploadSyllabus);

// Get full graph for a syllabus
syllabusRouter.get('/syllabus/:syllabusId/graph', getSyllabusGraph);

// Query the GraphRAG system
syllabusRouter.post('/syllabus/query', querySyllabus);

// Get prerequisite chain for a topic
syllabusRouter.get('/syllabus/:syllabusId/prerequisites/:topic', getPrerequisites);
