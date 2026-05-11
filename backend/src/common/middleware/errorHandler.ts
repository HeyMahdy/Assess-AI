import type { ErrorRequestHandler } from 'express';
import { logger } from '../../lib/logger.js';

function getHttpStatus(err: unknown): number {
  if (typeof err === 'object' && err !== null && 'status' in err) {
    const status = Reflect.get(err, 'status');
    if (typeof status === 'number' && Number.isFinite(status)) {
      return status;
    }
  }
  return 500;
}

function getErrorMessage(err: unknown, status: number): string {
  if (status !== 500) {
    if (typeof err === 'object' && err !== null && 'message' in err) {
      const message = Reflect.get(err, 'message');
      if (typeof message === 'string') {
        return message;
      }
    }
  }
  return 'Internal Server Error';
}

export const errorHandler: ErrorRequestHandler = (err, _req, res, _next) => {
  logger.error({ err }, 'unhandled error');
  const status = getHttpStatus(err);
  const message = getErrorMessage(err, status);
  res.status(status).json({ message });
};
