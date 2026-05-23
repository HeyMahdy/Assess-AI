const assignmentSchema = {
  type: 'object',
  properties: {
    id: { type: 'string' },
    title: { type: 'string' },
    subject: { type: 'string' },
    total_marks: { type: 'number' },
  },
  required: ['id', 'title', 'subject', 'total_marks'],
} as const;

const errorSchema = {
  type: 'object',
  properties: { message: { type: 'string' } },
  required: ['message'],
} as const;

export const assignmentPaths = {
  '/assignments': {
    post: {
      tags: ['Assignments'],
      summary: 'Create assignment',
      security: [{ bearerAuth: [] }],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              required: ['title', 'subject', 'total_marks'],
              properties: {
                title: { type: 'string' },
                subject: { type: 'string' },
                total_marks: { type: 'number' },
              },
            },
          },
        },
      },
      responses: {
        '201': {
          description: 'Created assignment',
          content: { 'application/json': { schema: assignmentSchema } },
        },
        '400': {
          description: 'Validation error',
          content: { 'application/json': { schema: errorSchema } },
        },
        '500': {
          description: 'Database error',
          content: { 'application/json': { schema: errorSchema } },
        },
      },
    },
  },
  '/assignments/{assignmentId}': {
    get: {
      tags: ['Assignments'],
      summary: 'Get assignment by id',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'assignmentId',
          in: 'path',
          required: true,
          schema: { type: 'string' },
        },
      ],
      responses: {
        '200': {
          description: 'Assignment',
          content: { 'application/json': { schema: assignmentSchema } },
        },
        '404': {
          description: 'Assignment not found',
          content: { 'application/json': { schema: errorSchema } },
        },
        '500': {
          description: 'Database error',
          content: { 'application/json': { schema: errorSchema } },
        },
      },
    },
    patch: {
      tags: ['Assignments'],
      summary: 'Update assignment',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'assignmentId',
          in: 'path',
          required: true,
          schema: { type: 'string' },
        },
      ],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              properties: {
                title: { type: 'string' },
                subject: { type: 'string' },
                total_marks: { type: 'number' },
              },
              minProperties: 1,
            },
          },
        },
      },
      responses: {
        '200': {
          description: 'Updated assignment',
          content: { 'application/json': { schema: assignmentSchema } },
        },
        '404': {
          description: 'Assignment not found',
          content: { 'application/json': { schema: errorSchema } },
        },
        '500': {
          description: 'Database error',
          content: { 'application/json': { schema: errorSchema } },
        },
      },
    },
    delete: {
      tags: ['Assignments'],
      summary: 'Delete assignment',
      security: [{ bearerAuth: [] }],
      parameters: [
        {
          name: 'assignmentId',
          in: 'path',
          required: true,
          schema: { type: 'string' },
        },
      ],
      responses: {
        '200': {
          description: 'Assignment deleted successfully',
          content: { 'application/json': { schema: errorSchema } },
        },
        '404': {
          description: 'Assignment not found',
          content: { 'application/json': { schema: errorSchema } },
        },
        '500': {
          description: 'Database error',
          content: { 'application/json': { schema: errorSchema } },
        },
      },
    },
  },
} as const;