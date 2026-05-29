const studentSchema = {
  type: 'object',
  properties: {
    teacher_id: { type: 'string', format: 'uuid' },
    id: { type: 'string', format: 'uuid' },
    student_id: { type: 'string' },
    studentId: { type: 'string' },
    name: { type: 'string' },
    created_at: { type: 'string', format: 'date-time' },
  },
  required: ['teacher_id', 'id', 'student_id', 'name'],
} as const;

const studentErrorSchema = {
  type: 'object',
  properties: { 
    error: { type: 'string' },
    details: { type: 'string', nullable: true }
  },
  required: ['error'],
} as const;

export const studentPaths: Record<string, any> = {
  '/students': {
    post: {
      tags: ['Students'],
      summary: 'Add a new student',
      description: 'Creates a new student record for the authenticated teacher.',
      security: [{ bearerAuth: [] }],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              required: ['student_id', 'name'],
              properties: {
                student_id: { 
                  type: 'string',
                  description: 'Teacher-facing student identifier (e.g., student ID number)'
                },
                name: { 
                  type: 'string',
                  description: 'Full name of the student'
                },
              },
            },
          },
        },
      },
      responses: {
        '201': {
          description: 'Student added successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: studentSchema,
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '400': {
          description: 'Bad Request: Missing required fields',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '409': {
          description: 'Conflict: Student with this ID already exists',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
    get: {
      tags: ['Students'],
      summary: 'Get all students for the authenticated teacher',
      description: 'Retrieves all students belonging to the authenticated teacher.',
      security: [{ bearerAuth: [] }],
      responses: {
        '200': {
          description: 'Students retrieved successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  count: { type: 'integer' },
                  data: {
                    type: 'array',
                    items: studentSchema,
                  },
                },
                required: ['message', 'count', 'data'],
              },
            },
          },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
  },
  '/students/search': {
    get: {
      tags: ['Students'],
      summary: 'Search students by ID or name',
      description: 'Searches students belonging to the authenticated teacher using case-insensitive partial matches on student_id and/or name.',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'student_id',
          in: 'query',
          required: false,
          schema: { type: 'string' },
          description: 'Partial or full teacher-facing student identifier',
        },
        {
          name: 'name',
          in: 'query',
          required: false,
          schema: { type: 'string' },
          description: 'Partial or full student name',
        },
      ],
      responses: {
        '200': {
          description: 'Students retrieved successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  count: { type: 'integer' },
                  data: {
                    type: 'array',
                    items: studentSchema,
                  },
                },
                required: ['message', 'count', 'data'],
              },
            },
          },
        },
        '400': {
          description: 'Bad Request: Missing search query',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
  },
  '/students/{studentId}': {
    get: {
      tags: ['Students'],
      summary: 'Get a specific student by ID',
      description: 'Retrieves a specific student belonging to the authenticated teacher.',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'studentId',
          in: 'path',
          required: true,
          schema: { type: 'string', format: 'uuid' },
          description: 'The student UUID primary key',
        },
      ],
      responses: {
        '200': {
          description: 'Student retrieved successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: studentSchema,
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '404': {
          description: 'Not Found: Student not found or unauthorized',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
    patch: {
      tags: ['Students'],
      summary: 'Update a student\'s information',
      description: 'Updates a specific student belonging to the authenticated teacher.',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'studentId',
          in: 'path',
          required: true,
          schema: { type: 'string', format: 'uuid' },
          description: 'The student UUID primary key',
        },
      ],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                student_id: { 
                  type: 'string',
                  description: 'Updated teacher-facing student identifier'
                },
                name: { 
                  type: 'string',
                  description: 'Updated full name of the student'
                },
              },
            },
          },
        },
      },
      responses: {
        '200': {
          description: 'Student updated successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: studentSchema,
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '404': {
          description: 'Not Found: Student not found or unauthorized',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
    delete: {
      tags: ['Students'],
      summary: 'Delete a student',
      description: 'Deletes a specific student belonging to the authenticated teacher.',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'studentId',
          in: 'path',
          required: true,
          schema: { type: 'string', format: 'uuid' },
          description: 'The student UUID primary key',
        },
      ],
      responses: {
        '200': {
          description: 'Student deleted successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: studentSchema,
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '401': {
          description: 'Unauthorized: Missing teacher identity',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '404': {
          description: 'Not Found: Student not found or unauthorized',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
        '500': {
          description: 'Internal Server Error: Database error',
          content: { 'application/json': { schema: studentErrorSchema } },
        },
      },
    },
  },
};
