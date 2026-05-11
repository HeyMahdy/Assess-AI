process.env.NODE_ENV = 'test';
process.env.PORT = '0';

process.env.DATABASE_HOST = '127.0.0.1';
process.env.DATABASE_PORT = '5432';
process.env.DATABASE_NAME = 'postgres';
process.env.DATABASE_USER = 'postgres';
process.env.DATABASE_PASSWORD = 'test';
process.env.DATABASE_URL = 'postgresql://postgres:test@127.0.0.1:5432/postgres';

process.env.UPSTASH_REDIS_REST_URL = 'https://example.upstash.io';
process.env.UPSTASH_REDIS_REST_TOKEN = 'test-token';
