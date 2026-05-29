const taChatErrorSchema = {
  type: 'object',
  properties: {
    error: { type: 'string' },
    details: { type: 'string', nullable: true },
  },
  required: ['error'],
};

export const taChatPaths: Record<string, any> = {
  '/ta/chat': {
    post: {
      tags: ['TA Chatbot'],
      summary: 'Send a message to the AI Teaching Assistant',
      description: 'The TA agent analyzes student performance, maps weaknesses to syllabus topics, and generates personalized study plans.',
      security: [{ bearerAuth: [] }],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              required: ['message'],
              properties: {
                message: {
                  type: 'string',
                  description: 'The teacher\'s message (e.g., "How did Mahdy do on the Physics assignment?")',
                },
                history: {
                  type: 'array',
                  description: 'Previous conversation messages for context',
                  items: {
                    type: 'object',
                    properties: {
                      role: { type: 'string', enum: ['user', 'assistant'] },
                      content: { type: 'string' },
                    },
                  },
                },
              },
            },
          },
        },
      },
      responses: {
        '200': {
          description: 'TA response generated',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    properties: {
                      response: { type: 'string', description: 'The AI Teaching Assistant\'s response with study plan' },
                    },
                  },
                },
                required: ['message', 'data'],
              },
            },
          },
        },
        '400': { description: 'Missing message', content: { 'application/json': { schema: taChatErrorSchema } } },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: taChatErrorSchema } } },
        '500': { description: 'Agent failed', content: { 'application/json': { schema: taChatErrorSchema } } },
      },
    },
  },
};
