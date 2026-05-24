import { Request, Response } from 'express';
import { pool } from '../lib/database.js';

/**
 * Add a new student for a teacher
 */
export const addStudent = async (req: Request, res: Response) => {
  try {
    const { id, name } = req.body;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    if (!id || !name) {
      return res.status(400).json({ error: 'Student ID and name are required' });
    }

    // Insert new student
    const query = `
      INSERT INTO public.students (teacher_id, id, name)
      VALUES ($1, $2, $3)
      RETURNING teacher_id, id, name, created_at;
    `;

    const result = await pool.query(query, [teacherId, id, name]);

    return res.status(201).json({
      message: 'Student added successfully',
      data: result.rows[0]
    });

  } catch (error: any) {
    // Handle duplicate key error
    if (error.code === '23505') {
      return res.status(409).json({ 
        error: 'Student with this ID already exists for this teacher',
        details: error.message 
      });
    }
    
    console.error('Error adding student:', error.message);
    return res.status(500).json({ 
      error: 'Database error', 
      details: error.message 
    });
  }
};

/**
 * Get all students for a teacher
 */
export const getStudentsByTeacher = async (req: Request, res: Response) => {
  try {
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    // Query to fetch all students for this teacher
    const query = `
      SELECT teacher_id, id, name, created_at 
      FROM public.students 
      WHERE teacher_id = $1
      ORDER BY name ASC;
    `;

    const result = await pool.query(query, [teacherId]);

    return res.status(200).json({
      message: 'Students retrieved successfully',
      count: result.rowCount ?? (result.rows ? result.rows.length : 0),
      data: result.rows
    });

  } catch (error: any) {
    console.error('Error fetching students:', error.message);
    return res.status(500).json({ 
      error: 'Database error', 
      details: error.message 
    });
  }
};

/**
 * Get a specific student by ID
 */
export const getStudentById = async (req: Request, res: Response) => {
  try {
    const { studentId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    // Query to fetch specific student
    const query = `
      SELECT teacher_id, id, name, created_at 
      FROM public.students 
      WHERE teacher_id = $1 AND id = $2;
    `;

    const result = await pool.query(query, [teacherId, studentId]);

    if (!result.rows || result.rows.length === 0) {
      return res.status(404).json({ 
        error: 'Student not found or you are not authorized to view it' 
      });
    }

    return res.status(200).json({
      message: 'Student retrieved successfully',
      data: result.rows[0]
    });

  } catch (error: any) {
    console.error('Error fetching student:', error.message);
    return res.status(500).json({ 
      error: 'Database error', 
      details: error.message 
    });
  }
};

/**
 * Update a student's information
 */
export const updateStudent = async (req: Request, res: Response) => {
  try {
    const { studentId } = req.params;
    const { name } = req.body;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    // Validate that name is provided and not empty
    if (!name || String(name).trim() === '') {
      const existingQuery = `
        SELECT teacher_id, id, name, created_at 
        FROM public.students 
        WHERE teacher_id = $1 AND id = $2;
      `;
      const fallbackResult = await pool.query(existingQuery, [teacherId, studentId]);
      
      if (!fallbackResult.rows || fallbackResult.rows.length === 0) {
        return res.status(404).json({ error: 'Student not found' });
      }

      return res.status(200).json({
        message: 'No modifications requested. Student remained unchanged.',
        data: fallbackResult.rows[0]
      });
    }

    // Update student name
    const query = `
      UPDATE public.students 
      SET name = $1
      WHERE teacher_id = $2 AND id = $3
      RETURNING teacher_id, id, name, created_at;
    `;

    const result = await pool.query(query, [name, teacherId, studentId]);

    if (!result.rows || result.rows.length === 0) {
      return res.status(404).json({ 
        error: 'Student not found or you are not authorized to modify it' 
      });
    }

    return res.status(200).json({
      message: 'Student updated successfully',
      data: result.rows[0]
    });

  } catch (error: any) {
    console.error('Error updating student:', error.message);
    return res.status(500).json({ 
      error: 'Database error', 
      details: error.message 
    });
  }
};

/**
 * Delete a student
 */
export const deleteStudent = async (req: Request, res: Response) => {
  try {
    const { studentId } = req.params;
    const teacherId = req.authUser?.id;

    if (!teacherId) {
      return res.status(401).json({ error: 'Unauthorized: Missing teacher identity' });
    }

    // Delete student
    const query = `
      DELETE FROM public.students 
      WHERE teacher_id = $1 AND id = $2
      RETURNING teacher_id, id, name;
    `;

    const result = await pool.query(query, [teacherId, studentId]);

    if (!result.rows || result.rows.length === 0) {
      return res.status(404).json({ 
        error: 'Student not found or you are not authorized to delete it' 
      });
    }

    return res.status(200).json({
      message: 'Student deleted successfully',
      data: result.rows[0]
    });

  } catch (error: any) {
    console.error('Error deleting student:', error.message);
    return res.status(500).json({ 
      error: 'Database error', 
      details: error.message 
    });
  }
};
