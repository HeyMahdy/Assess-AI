const syllabusErrorSchema = {
  type: 'object',
  properties: {
    error: { type: 'string' },
    details: { type: 'string', nullable: true },
  },
  required: ['error'],
};

export const syllabusPaths: Record<string, any> = {
  '/syllabus/upload': {
    post: {
      tags: ['Syllabus GraphRAG'],
      summary: 'Upload a syllabus and trigger GraphRAG ingestion',
      description: 'Accepts a PDF, DOCX, or TXT file. Extracts entities and relationships using AI, stores them with vector embeddings for semantic search.',
      security: [{ bearerAuth: [] }],
      requestBody: {
        required: true,
        content: {
          'multipart/form-data': {
            schema: {
              type: 'object',
              required: ['file'],
              properties: {
                file: {
                  type: 'string',
                  format: 'binary',
                  description: 'Syllabus file (PDF, DOCX, or TXT)',
                },
              },
            },
          },
        },
      },
      responses: {
        '202': {
          description: 'Syllabus upload accepted for processing',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    properties: {
                      syllabus_id: { type: 'integer' },
                      status: { type: 'string' },
                      entity_count: { type: 'integer' },
                      relationship_count: { type: 'integer' },
                    },
                  },
                },
              },
              example: {
                message: 'Syllabus upload accepted for processing',
                data: {
                  syllabus_id: 1,
                  status: 'completed',
                  entity_count: 22,
                  relationship_count: 18,
                },
              },
            },
          },
        },
        '400': { description: 'No file uploaded or text extraction failed', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '500': { description: 'Processing failed', content: { 'application/json': { schema: syllabusErrorSchema } } },
      },
    },
  },
  '/syllabus/{syllabusId}/status': {
    get: {
      tags: ['Syllabus GraphRAG'],
      summary: 'Get syllabus ingestion status',
      description: 'Returns the current ingestion status for a syllabus from the GraphRAG agent service.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'syllabusId', in: 'path', required: true, schema: { type: 'integer' } },
      ],
      responses: {
        '200': {
          description: 'Syllabus status retrieved',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    additionalProperties: true,
                    description: 'Status payload returned by the GraphRAG agent service.',
                  },
                },
                required: ['message', 'data'],
              },
              example: {
                message: 'Syllabus status retrieved',
                data: {
                  syllabus_id: 1,
                  status: 'completed',
                },
              },
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '500': { description: 'Failed to fetch syllabus status', content: { 'application/json': { schema: syllabusErrorSchema } } },
      },
    },
  },
  '/syllabus/{syllabusId}/graph': {
    get: {
      tags: ['Syllabus GraphRAG'],
      summary: 'Get the full entity-relationship graph for a syllabus',
      description: 'Returns all extracted topics (nodes) and their relationships (edges) for visualization.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'syllabusId', in: 'path', required: true, schema: { type: 'integer' } },
      ],
      responses: {
        '200': {
          description: 'Graph retrieved successfully',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    properties: {
                      nodes: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            id: { type: 'integer' },
                            name: { type: 'string' },
                            entity_type: { type: 'string' },
                            description: { type: 'string' },
                            difficulty_level: { type: 'string' },
                            week_or_unit: { type: 'string', nullable: true },
                          },
                        },
                      },
                      edges: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            id: { type: 'integer' },
                            source: { type: 'string' },
                            target: { type: 'string' },
                            relationship_type: { type: 'string' },
                            strength: { type: 'integer' },
                            reason: { type: 'string' },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '500': { description: 'Failed to fetch graph', content: { 'application/json': { schema: syllabusErrorSchema } } },
      },
    },
  },
  '/syllabus/query': {
    post: {
      tags: ['Syllabus GraphRAG'],
      summary: 'Query the syllabus using natural language',
      description: 'Performs vector search to find matching topics, retrieves graph relationships, and synthesizes an answer using LLM.',
      security: [{ bearerAuth: [] }],
      requestBody: {
        required: true,
        content: {
          'application/json': {
            schema: {
              type: 'object',
              required: ['query', 'syllabus_id'],
              properties: {
                query: { type: 'string', description: 'Natural language question about the syllabus' },
                syllabus_id: { type: 'integer', description: 'The syllabus to query against' },
              },
            },
          },
        },
      },
      responses: {
        '200': {
          description: 'Query completed',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    properties: {
                      answer: { type: 'string' },
                      matched_entities: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            name: { type: 'string' },
                            type: { type: 'string' },
                            similarity: { type: 'number' },
                          },
                        },
                      },
                      prerequisites: { type: 'array', items: { type: 'string' } },
                      related_topics: { type: 'array', items: { type: 'string' } },
                    },
                  },
                },
              },
            },
          },
        },
        '400': { description: 'Missing query or syllabus_id', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '500': { description: 'Query failed', content: { 'application/json': { schema: syllabusErrorSchema } } },
      },
    },
  },
  '/syllabus/{syllabusId}/prerequisites/{topic}': {
    get: {
      tags: ['Syllabus GraphRAG'],
      summary: 'Get the full prerequisite chain for a topic',
      description: 'Recursively traverses the graph to return all prerequisites from foundational to advanced.',
      security: [{ bearerAuth: [] }],
      parameters: [
        { name: 'syllabusId', in: 'path', required: true, schema: { type: 'integer' } },
        { name: 'topic', in: 'path', required: true, schema: { type: 'string' }, description: 'The topic name to find prerequisites for' },
      ],
      responses: {
        '200': {
          description: 'Prerequisites retrieved',
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  message: { type: 'string' },
                  data: {
                    type: 'object',
                    properties: {
                      topic: { type: 'string' },
                      prerequisite_chain: {
                        type: 'array',
                        items: {
                          type: 'object',
                          properties: {
                            name: { type: 'string' },
                            entity_type: { type: 'string' },
                            difficulty_level: { type: 'string' },
                            depth: { type: 'integer' },
                          },
                        },
                      },
                    },
                  },
                },
              },
            },
          },
        },
        '401': { description: 'Unauthorized', content: { 'application/json': { schema: syllabusErrorSchema } } },
        '500': { description: 'Failed to fetch prerequisites', content: { 'application/json': { schema: syllabusErrorSchema } } },
      },
    },
  },
};
