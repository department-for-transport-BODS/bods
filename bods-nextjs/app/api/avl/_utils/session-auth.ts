import type { NextRequest } from 'next/server';

export function getSessionHeaders(request: NextRequest, options?: { includeCsrf?: boolean }): Headers {
  const headers = new Headers();
  const cookieHeader = request.headers.get('cookie');

  if (cookieHeader) {
    headers.set('cookie', cookieHeader);
  }

  if (options?.includeCsrf) {
    const csrfHeader = request.headers.get('x-csrftoken') || request.headers.get('X-CSRFToken');
    if (csrfHeader) {
      headers.set('X-CSRFToken', csrfHeader);
    }
  }

  return headers;
}

export function hasSessionCookie(request: NextRequest): boolean {
  return Boolean(request.headers.get('cookie'));
}