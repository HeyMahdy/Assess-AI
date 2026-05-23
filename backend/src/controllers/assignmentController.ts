import {pool} from '../lib/database.js'

import { Request, Response } from 'express';

export const createAssignment = async (req: Request, res: Response) => {
  const { title, subject, total_marks } = req.body;
  const teacherId = req.authUser?.id
  if (!teacherId) {
    return res.status(401).json({ message: 'Unauthorized' });
  }
  try {
    const query = `
      INSERT INTO assignments (title, subject, teacher_id, total_marks)
      VALUES ($1, $2, $3, $4)
      RETURNING id
    `;
    const result = await pool.query(query, [title, subject, teacherId, total_marks]);
    
    return res.status(201).json({
      assignment_id: result.rows[0].id,
      message: "Assignment created successfully"
    });
  } catch (err) {
    console.log(err)
    return res.status(500).json({ error: 'Database error while creating assignment' });
  }
};

// GET /assignments/:assignmentId
export const getAssignmentById = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  try {
    const query = 'SELECT id as assignment_id, title, subject, topic, total_marks FROM assignments WHERE id = $1';
    const result = await pool.query(query, [assignmentId]);
    
    if (result.rows.length === 0) return res.status(404).json({ message: 'Assignment not found' });
    return res.json(result.rows[0]);
  } catch (err) {
    return res.status(500).json({ error: 'Database error while fetching assignment' });
  }
};

// PATCH /assignments/:assignmentId
export const updateAssignment = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  const { title, topic } = req.body;
  try {
    const query = 'UPDATE assignments SET title = $1, topic = $2 WHERE id = $3 RETURNING *';
    const result = await pool.query(query, [title, topic, assignmentId]);
    
    if (result.rows.length === 0) return res.status(404).json({ message: 'Assignment not found' });
    return res.json(result.rows[0]);
  } catch (err) {
    return res.status(500).json({ error: 'Database error while updating assignment' });
  }
};

// DELETE /assignments/:assignmentId
export const deleteAssignment = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  try {
    const query = 'DELETE FROM assignments WHERE id = $1';
    const result = await pool.query(query, [assignmentId]);
    
    if (result.rowCount === 0) return res.status(404).json({ message: 'Assignment not found' });
    return res.json({ message: 'Assignment deleted successfully' });
  } catch (err) {
    return res.status(500).json({ error: 'Database error while deleting assignment' });
  }
};