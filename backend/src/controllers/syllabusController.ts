import { Request, Response } from 'express';
import axios from 'axios';
import FormData from 'form-data';

const FASTAPI_URL = 'http://localhost:8000';

/**
 * Upload a syllabus and trigger GraphRAG ingestion
 */
export const uploadSyllabus = async (req: Request, res: Response) => {
  try {
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    const file = (req as any).file as any;

    if (!file) {
      return res.status(400).json({ error: 'No file uploaded' });
    }

    const formData = new FormData();
    formData.append('file', file.buffer, file.originalname);
    formData.append('teacher_id', teacherId);

    const response = await axios.post(`${FASTAPI_URL}/internal/agent/syllabus/upload`, formData, {
      headers: { ...formData.getHeaders() },
    });

    return res.status(202).json({
      message: 'Syllabus upload accepted for processing',
      data: response.data
    });

  } catch (error: any) {
    console.error('Error uploading syllabus:', error.message);
    return res.status(500).json({
      error: 'Failed to process syllabus',
      details: error.response?.data || error.message
    });
  }
};

/**
 * Get syllabus ingestion status
 */
export const getSyllabusStatus = async (req: Request, res: Response) => {
  try {
    const { syllabusId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    const response = await axios.get(`${FASTAPI_URL}/internal/agent/syllabus/${syllabusId}/status`);

    return res.status(200).json({
      message: 'Syllabus status retrieved',
      data: response.data
    });

  } catch (error: any) {
    console.error('Error fetching syllabus status:', error.message);
    return res.status(500).json({
      error: 'Failed to fetch syllabus status',
      details: error.response?.data || error.message
    });
  }
};

/**
 * Get the full graph for a syllabus
 */
export const getSyllabusGraph = async (req: Request, res: Response) => {
  try {
    const { syllabusId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    const response = await axios.get(`${FASTAPI_URL}/internal/agent/syllabus/${syllabusId}/graph`);

    return res.status(200).json({
      message: 'Graph retrieved successfully',
      data: response.data
    });

  } catch (error: any) {
    console.error('Error fetching graph:', error.message);
    return res.status(500).json({
      error: 'Failed to fetch graph',
      details: error.response?.data || error.message
    });
  }
};

/**
 * Query the GraphRAG system
 */
export const querySyllabus = async (req: Request, res: Response) => {
  try {
    const { query, syllabus_id } = req.body;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    if (!query || !syllabus_id) {
      return res.status(400).json({ error: 'query and syllabus_id are required' });
    }

    const response = await axios.post(`${FASTAPI_URL}/internal/agent/syllabus/query`, {
      query,
      syllabus_id: Number(syllabus_id),
    });

    return res.status(200).json({
      message: 'Query completed',
      data: response.data
    });

  } catch (error: any) {
    console.error('Error querying syllabus:', error.message);
    return res.status(500).json({
      error: 'Failed to query syllabus',
      details: error.response?.data || error.message
    });
  }
};

/**
 * Get prerequisite chain for a topic
 */
export const getPrerequisites = async (req: Request, res: Response) => {
  try {
    const { syllabusId, topic } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    if (typeof topic !== 'string') {
      return res.status(400).json({ error: 'topic is required' });
    }

    const response = await axios.get(
      `${FASTAPI_URL}/internal/agent/syllabus/${syllabusId}/prerequisites/${encodeURIComponent(topic)}`
    );

    return res.status(200).json({
      message: 'Prerequisites retrieved',
      data: response.data
    });

  } catch (error: any) {
    console.error('Error fetching prerequisites:', error.message);
    return res.status(500).json({
      error: 'Failed to fetch prerequisites',
      details: error.response?.data || error.message
    });
  }
};
