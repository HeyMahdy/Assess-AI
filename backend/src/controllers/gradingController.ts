import { Request, Response } from 'express';
import axios from 'axios';
import { pool } from '../lib/database.js';

/**
 * Trigger grading for a student's assignment
 */
export const startGrading = async (req: Request, res: Response) => {
  try {
    const { assignmentId, studentId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    const FASTAPI_URL = 'http://localhost:8000';

    const response = await axios.post(`${FASTAPI_URL}/internal/agent/grade/process`, {
      teacher_id: teacherId,
      student_id: studentId,
      assignment_id: Number(assignmentId),
    });

    const agentResult = response.data;

    return res.status(200).json({
      message: 'Grading completed successfully',
      data: agentResult.results
    });

  } catch (error: any) {
    console.error('Error communicating with Grading Agent service:', error.message);
    return res.status(500).json({
      error: 'Failed to process grading',
      details: error.response?.data || error.message
    });
  }
};

/**
 * Get grading results for a student on an assignment
 */
export const getGradingResults = async (req: Request, res: Response) => {
  try {
    const { assignmentId, studentId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    const query = `
      SELECT id, question_label, student_solution, marks, confidence_score, created_at, updated_at
      FROM public.student_question_scores
      WHERE assignment_id = $1 AND student_id = $2 AND teacher_id = $3
      ORDER BY id ASC;
    `;

    const result = await pool.query(query, [assignmentId, studentId, teacherId]);

    // Calculate total
    let totalMarks = 0;
    for (const row of result.rows) {
      totalMarks += parseFloat(row.marks);
    }

    return res.status(200).json({
      message: 'Grading results retrieved successfully',
      count: result.rowCount ?? result.rows.length,
      total_marks: totalMarks,
      data: result.rows
    });

  } catch (error: any) {
    console.error('Error fetching grading results:', error.message);
    return res.status(500).json({
      error: 'Database error',
      details: error.message
    });
  }
};
