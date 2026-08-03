import type { NextRequest } from 'next/server';
import { HOSTS } from '@/config';

const SESSION_COOKIE_PATTERN = /(?:^|;\s*)sessionid=[^;]+/;

export function getSessionHeaders(
  request: NextRequest,
  options?: { includeCsrf?: boolean },
): Headers {
  const headers = new Headers();
  const cookieHeader = request.headers.get('cookie');

  if (cookieHeader) {
    headers.set('cookie', cookieHeader);
  }

  if (options?.includeCsrf) {
    const csrfHeader =
      request.headers.get('x-csrftoken') || request.headers.get('X-CSRFToken');
    if (csrfHeader) {
      headers.set('X-CSRFToken', csrfHeader);
    }
  }

  const publishHost = new URL(HOSTS.publish).host;
  headers.set('host', publishHost);
  headers.set('x-forwarded-host', publishHost);

  return headers;
}

export function hasSessionCookie(request: NextRequest): boolean {
  const cookieHeader = request.headers.get('cookie');
  return Boolean(cookieHeader && SESSION_COOKIE_PATTERN.test(cookieHeader));
}
