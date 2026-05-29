const scoreSchema = {
  type: 'object',
  properties: {
    id: { type: 'integer' },
    question_label: { type: 'string' },
    student_solution: { type: 'string' },
    marks: { type: 'number' },
    confidence_score: { type: 'number' },
    teacher_comment: { type: 'string', nullable: true },
    created_at: { type: 'string', format: 'date-time' },
    updated_at: { type: 'string', format: 'date-time' },
  },
  required: ['id', 'question_label', 'marks', 'confidence_score'],
};

const gradingErrorSchema = {
  type: 'object',
  properties: {
    error: { type: 'string' },
    details: { type: 'string', nullable: true },
  },
  required: ['error'],
};

export const gradingPaths: Record<string, any> = {
  '/assignments/{assignmentId}/students/{studentId}/grade': {
    post: {
      tags: ['Grading'],
      summary: 'Trigger AI grading for a student on an assignment',
      description: 'Runs the dual-grader AI agent to evaluate all student answers for the given assignment and stores scores in the database.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'assignmentId', in: 'path', required: true, schema: { type: 'string' } },
        { name: 'studentId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
      ],
      responses: {
        '200': {
          description: 'Grading completed successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'array',
                    items: {
                      type: 'object',
                      properties: {
                        label: { type: 'string' },
                        grader_1_score: { type: 'number' },
                        grader_2_score: { type: 'number' },
                        final_score: { type: 'number' },
                        confidence: { type: 'number' },
                        confidence_label: { type: 'string', enum: ['high', 'medium', 'low'] },
                      },
                    },
                  },
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: gradingErrorSchema } } },
        '500': { description: 'Grading failed', content: { 'application/json': { schema: gradingErrorSchema } } },
      },
    },
  },
  '/assignments/{assignmentId}/students/{studentId}/scores': {
    get: {
      tags: ['Grading'],
      summary: 'Get grading results for a student on an assignment',
      description: 'Retrieves all stored scores from the student_question_scores table.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'assignmentId', in: 'path', required: true, schema: { type: 'string' } },
        { name: 'studentId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
      ],
      responses: {
        '200': {
          description: 'Grading results retrieved successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  count: { type: 'integer' },
                  total_marks: { type: 'number' },
                  data: { type: 'array', items: scoreSchema },
                },
                required: ['message', 'count', 'total_marks', 'data'],
              },
              example: {
                message: 'Grading results retrieved successfully',
                count: 1,
                total_marks: 4.25,
                data: [
                  {
                    id: 1,
                    question_label: '1a',
                    student_solution: 'Student solution text.',
                    marks: 4.25,
                    confidence_score: 0.89,
                    teacher_comment: null,
                    created_at: '2026-05-29T17:25:38.376Z',
                    updated_at: '2026-05-29T17:25:38.376Z',
                  },
                ],
              },
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: gradingErrorSchema } } },
        '500': { description: 'Database error', content: { 'application/json': { schema: gradingErrorSchema } } },
      },
    },
  },
  '/assignments/{assignmentId}/students/{studentId}/scores/{scoreId}': {
    patch: {
      tags: ['Grading'],
      summary: 'Update a grading result after teacher review',
      description: 'Allows the authenticated teacher to override marks and add or edit a teacher comment for one stored score row.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'assignmentId', in: 'path', required: true, schema: { type: 'string' } },
        { name: 'studentId', in: 'path', required: true, schema: { type: 'string', format: 'uuid' } },
        { name: 'scoreId', in: 'path', required: true, schema: { type: 'string' } },
      ],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                marks: { type: 'number', minimum: 0 },
                teacher_comment: { type: 'string', nullable: true },
              },
              minProperties: 1,
            },
            example: {
              marks: 2.5,
              teacher_comment: 'Accepted alternate reasoning but final unit is missing.',
            },
          },
        },
      },
      responses: {
        '200': {
          description: 'Grading result updated successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: scoreSchema,
                },
                required: ['message', 'data'],
              },
              example: {
                message: 'Grading result updated successfully',
                data: {
                  id: 1,
                  question_label: '1a',
                  student_solution: 'Student solution text.',
                  marks: 4.5,
                  confidence_score: 0.89,
                  teacher_comment: 'Accepted alternate reasoning.',
                  created_at: '2026-05-29T17:25:38.376Z',
                  updated_at: '2026-05-29T17:30:12.000Z',
                },
              },
            },
          },
        },
        '400': { description: 'Invalid update payload', content: { 'application/json': { schema: gradingErrorSchema } } },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: gradingErrorSchema } } },
        '404': { description: 'Grading result not found', content: { 'application/json': { schema: gradingErrorSchema } } },
        '500': { description: 'Database error', content: { 'application/json': { schema: gradingErrorSchema } } },
      },
    },
  },
};
