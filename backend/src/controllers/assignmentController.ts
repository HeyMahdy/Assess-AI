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

// GET /assignments
export const getAssignments = async (req: Request, res: Response) => {
  const teacherId = req.authUser?.id;

  if (!teacherId) {
    return res.status(401).json({ message: 'Unauthorized' });
  }

  try {
    const query = `
      SELECT id as assignment_id, title, subject, total_marks, created_at
      FROM assignments
      WHERE teacher_id = $1
      ORDER BY created_at DESC, id DESC
    `;

    const result = await pool.query(query, [teacherId]);

    return res.status(200).json({
      message: 'Assignments retrieved successfully',
      count: result.rowCount ?? result.rows.length,
      data: result.rows
    });
  } catch (err: any) {
    console.error('Error fetching assignments:', err);
    return res.status(500).json({
      error: 'Database error while fetching assignments',
      details: err.message
    });
  }
};

// GET /assignments/:assignmentId
export const getAssignmentById = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  try {
    const query = 'SELECT id as assignment_id, title, subject, total_marks, created_at FROM assignments WHERE id = $1';
    const result = await pool.query(query, [assignmentId]);
    
    if (result.rows.length === 0) return res.status(404).json({ message: 'Assignment not found' });
    return res.json(result.rows[0]);
  } catch (err: any) {
    console.error('Error fetching assignment:', err);
    return res.status(500).json({ error: 'Database error while fetching assignment', details: err.message });
  }
};

// PATCH /assignments/:assignmentId
export const updateAssignment = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  const { title, subject, total_marks } = req.body;
  
  try {
    // Build dynamic update query
    const setFields: string[] = [];
    const queryValues: any[] = [];
    let paramIndex = 1;

    if (title !== undefined && title !== null && String(title).trim() !== '') {
      setFields.push(`title = $${paramIndex++}`);
      queryValues.push(title);
    }

    if (subject !== undefined && subject !== null && String(subject).trim() !== '') {
      setFields.push(`subject = $${paramIndex++}`);
      queryValues.push(subject);
    }

    if (total_marks !== undefined && total_marks !== null) {
      setFields.push(`total_marks = $${paramIndex++}`);
      queryValues.push(Number(total_marks));
    }

    if (setFields.length === 0) {
      const existingQuery = 'SELECT * FROM assignments WHERE id = $1';
      const fallbackResult = await pool.query(existingQuery, [assignmentId]);
      
      if (fallbackResult.rows.length === 0) {
        return res.status(404).json({ message: 'Assignment not found' });
      }

      return res.status(200).json({
        message: 'No modifications requested. Assignment remained unchanged.',
        data: fallbackResult.rows[0]
      });
    }

    queryValues.push(assignmentId);
    const assignmentIdParam = `$${paramIndex++}`;

    const query = `
      UPDATE assignments 
      SET ${setFields.join(', ')}
      WHERE id = ${assignmentIdParam}
      RETURNING *
    `;

    const result = await pool.query(query, queryValues);
    
    if (result.rows.length === 0) {
      return res.status(404).json({ message: 'Assignment not found' });
    }
    
    return res.json(result.rows[0]);
  } catch (err: any) {
    console.error('Error updating assignment:', err);
    return res.status(500).json({ error: 'Database error while updating assignment', details: err.message });
  }
};

// DELETE /assignments/:assignmentId
export const deleteAssignment = async (req: Request, res: Response) => {
  const { assignmentId } = req.params;
  try {
    const query = 'DELETE FROM assignments WHERE id = $1';
    const result = await pool.query(query, [assignmentId]);
    
    if (result.rowCount === 0) {
      return res.status(404).json({ message: 'Assignment not found' });
    }
    
    return res.json({ message: 'Assignment deleted successfully' });
  } catch (err: any) {
    console.error('Error deleting assignment:', err);
    return res.status(500).json({ error: 'Database error while deleting assignment', details: err.message });
  }
};
