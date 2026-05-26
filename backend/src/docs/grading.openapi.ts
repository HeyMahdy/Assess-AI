const scoreSchema = {
  type: 'object',
  properties: {
    id: { type: 'integer' },
    question_label: { type: 'string' },
    student_solution: { type: 'string' },
    marks: { type: 'number' },
    confidence_score: { type: 'number' },
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
        { name: 'studentId', in: 'path', required: true, schema: { type: 'string' } },
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
        { name: 'studentId', in: 'path', required: true, schema: { type: 'string' } },
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
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: gradingErrorSchema } } },
        '500': { description: 'Database error', content: { 'application/json': { schema: gradingErrorSchema } } },
      },
    },
  },
};
