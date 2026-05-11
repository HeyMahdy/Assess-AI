const profileSchema = {
  type: 'object',
  properties: {
    id: { type: 'string', format: 'uuid' },
    display_name: { type: 'string', nullable: true },
    avatar_url: { type: 'string', nullable: true },
    role: { type: 'string', enum: ['student', 'teacher', 'admin'] },
  },
  required: ['id', 'display_name', 'avatar_url', 'role'],
} as const;

const sessionSchema = {
  type: 'object',
  properties: {
    access_token: { type: 'string' },
    refresh_token: { type: 'string' },
    expires_in: { type: 'integer' },
    expires_at: { type: 'integer', nullable: true },
    token_type: { type: 'string' },
    user: {
      type: 'object',
      properties: {
        id: { type: 'string', format: 'uuid' },
        email: { type: 'string', nullable: true },
        email_confirmed_at: { type: 'string', format: 'date-time', nullable: true },
      },
    },
  },
} as const;

const errorSchema = {
  type: 'object',
  properties: { message: { type: 'string' } },
  required: ['message'],
} as const;

export const openApiDocument = {
  openapi: '3.0.3',
  info: {
    title: 'Assess AI API',
    version: '1.0.0',
    description:
      'Auth uses Supabase. Protected routes send `Authorization: Bearer <access_token>`. Role claims for API authorization are loaded from `public.profiles` (not `user_metadata`).',
  },
  components: {
    securitySchemes: {
      bearerAuth: {
        type: 'http',
        scheme: 'bearer',
        bearerFormat: 'JWT',
        description: 'Supabase access token (JWT).',
      },
    },
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
    '/auth/signup': {
      post: {
        tags: ['Auth'],
        summary: 'Sign up with email and password',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['email', 'password'],
                properties: {
                  email: { type: 'string', format: 'email' },
                  password: { type: 'string', minLength: 8, maxLength: 128 },
                  display_name: { type: 'string', maxLength: 200 },
                },
              },
            },
          },
        },
        responses: {
          '201': {
            description:
              'User created. With Supabase “Confirm email” off, body matches login session. If confirmation is required, body is only `{ userId }`.',
            content: {
              'application/json': {
                schema: {
                  oneOf: [
                    sessionSchema,
                    {
                      type: 'object',
                      properties: { userId: { type: 'string', format: 'uuid', nullable: true } },
                      required: ['userId'],
                    },
                  ],
                },
              },
            },
          },
          '400': {
            description: 'Validation or signup error',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/auth/login': {
      post: {
        tags: ['Auth'],
        summary: 'Email/password login',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['email', 'password'],
                properties: {
                  email: { type: 'string', format: 'email' },
                  password: { type: 'string' },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Session',
            content: { 'application/json': { schema: sessionSchema } },
          },
          '401': {
            description: 'Invalid credentials',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/auth/password/forgot': {
      post: {
        tags: ['Auth'],
        summary: 'Request Supabase password reset email',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['email'],
                properties: { email: { type: 'string', format: 'email' } },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Email dispatched',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: { ok: { type: 'boolean' } },
                  required: ['ok'],
                },
              },
            },
          },
          '400': { description: 'Error', content: { 'application/json': { schema: errorSchema } } },
        },
      },
    },
    '/auth/password/reset': {
      post: {
        tags: ['Auth'],
        summary: 'Complete password reset using recovery OTP token from email',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['email', 'token', 'newPassword'],
                properties: {
                  email: { type: 'string', format: 'email' },
                  token: { type: 'string' },
                  newPassword: { type: 'string', minLength: 8, maxLength: 128 },
                },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Session after password change',
            content: { 'application/json': { schema: sessionSchema } },
          },
          '400': {
            description: 'Invalid token',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/auth/refresh': {
      post: {
        tags: ['Auth'],
        summary: 'Refresh session',
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                required: ['refresh_token'],
                properties: { refresh_token: { type: 'string' } },
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Session',
            content: { 'application/json': { schema: sessionSchema } },
          },
          '401': {
            description: 'Invalid refresh token',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/users/me': {
      get: {
        tags: ['Users'],
        summary: 'Get my profile',
        security: [{ bearerAuth: [] }],
        responses: {
          '200': {
            description: 'Profile',
            content: { 'application/json': { schema: profileSchema } },
          },
          '401': {
            description: 'Unauthorized',
            content: { 'application/json': { schema: errorSchema } },
          },
          '404': {
            description: 'Profile missing',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
      patch: {
        tags: ['Users'],
        summary: 'Update my profile (display fields only; roles are admin-only)',
        security: [{ bearerAuth: [] }],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  display_name: { type: 'string', nullable: true, maxLength: 200 },
                  avatar_url: { type: 'string', nullable: true, format: 'uri' },
                },
                additionalProperties: false,
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Updated profile',
            content: { 'application/json': { schema: profileSchema } },
          },
          '400': {
            description: 'Validation error',
            content: { 'application/json': { schema: errorSchema } },
          },
          '401': {
            description: 'Unauthorized',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/users': {
      get: {
        tags: ['Users'],
        summary: 'List users (admin)',
        security: [{ bearerAuth: [] }],
        parameters: [
          {
            name: 'limit',
            in: 'query',
            schema: { type: 'integer', minimum: 1, maximum: 100, default: 50 },
          },
          { name: 'offset', in: 'query', schema: { type: 'integer', minimum: 0, default: 0 } },
        ],
        responses: {
          '200': {
            description: 'Paged profiles',
            content: {
              'application/json': {
                schema: {
                  type: 'object',
                  properties: {
                    items: { type: 'array', items: profileSchema },
                    total: { type: 'integer' },
                  },
                  required: ['items', 'total'],
                },
              },
            },
          },
          '401': {
            description: 'Unauthorized',
            content: { 'application/json': { schema: errorSchema } },
          },
          '403': {
            description: 'Forbidden',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
    '/users/{userId}': {
      patch: {
        tags: ['Users'],
        summary: 'Update a user profile (admin)',
        security: [{ bearerAuth: [] }],
        parameters: [
          {
            name: 'userId',
            in: 'path',
            required: true,
            schema: { type: 'string', format: 'uuid' },
          },
        ],
        requestBody: {
          required: true,
          content: {
            'application/json': {
              schema: {
                type: 'object',
                properties: {
                  display_name: { type: 'string', nullable: true },
                  avatar_url: { type: 'string', nullable: true, format: 'uri' },
                  role: { type: 'string', enum: ['student', 'teacher', 'admin'] },
                },
                additionalProperties: false,
                minProperties: 1,
              },
            },
          },
        },
        responses: {
          '200': {
            description: 'Updated profile',
            content: { 'application/json': { schema: profileSchema } },
          },
          '400': {
            description: 'Validation error',
            content: { 'application/json': { schema: errorSchema } },
          },
          '401': {
            description: 'Unauthorized',
            content: { 'application/json': { schema: errorSchema } },
          },
          '403': {
            description: 'Forbidden',
            content: { 'application/json': { schema: errorSchema } },
          },
          '404': {
            description: 'User not found',
            content: { 'application/json': { schema: errorSchema } },
          },
        },
      },
    },
  },
} as const;
