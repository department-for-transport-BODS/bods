const djangoInternalOrigin = process.env.DJANGO_INTERNAL_ORIGIN || 'http://localhost:8000';

export const serverConfig = {
  djangoInternalOrigin,
} as const;