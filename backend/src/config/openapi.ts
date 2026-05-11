export const openApiDocument = {
  openapi: '3.0.3',
  info: {
    title: 'Assess AI API',
    version: '1.0.0',
  },
  paths: {
    '/health': {
      get: {
        summary: 'Health check',
        responses: {
          '200': {
            description: 'Service is healthy',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    status: { type: 'string', example: 'ok' },
                    timestamp: { type: 'string', format: 'date-time' },
                  },
                  required: ['status', 'timestamp'],
                },
              },
            },
          },
        },
      },
    },
  },
} as const;
