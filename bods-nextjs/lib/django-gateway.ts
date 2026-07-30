import type { NextRequest } from 'next/server';
import { HOSTS } from '@/config';
import { serverConfig } from '@/lib/server-config';

const BODYLESS_METHODS = new Set(['GET', 'HEAD']);
const REQUEST_HEADERS_TO_REMOVE = [
  'content-length',
  'host',
  'x-forwarded-host',
];

const DJANGO_NAMESPACES = {
  auth: {
    upstreamPrefix: '/api/auth/',
    upstreamHost: new URL(HOSTS.www).host,
  },
  data: {
    upstreamPrefix: '/api/',
    upstreamHost: new URL(HOSTS.data).host,
  },
  publish: {
    upstreamPrefix: '/api/',
    upstreamHost: new URL(HOSTS.publish).host,
  },
} as const;

export function getDjangoNamespace(namespace: string) {
  return DJANGO_NAMESPACES[namespace as keyof typeof DJANGO_NAMESPACES] ?? null;
}

export function djangoPath(
  prefix: string,
  path: string[],
  requestPathname: string,
): string {
  const encodedPath = path.map((segment) => encodeURIComponent(segment)).join('/');
  const trailingSlash = requestPathname.endsWith('/') ? '/' : '';
  return `${prefix}${encodedPath}${trailingSlash}`;
}

export async function forwardToDjango(
  request: NextRequest,
  upstreamPath: string,
  upstreamHost: string,
): Promise<Response> {
  const upstreamUrl = new URL(upstreamPath, serverConfig.djangoInternalOrigin);
  upstreamUrl.search = request.nextUrl.search;

  const headers = new Headers(request.headers);
  REQUEST_HEADERS_TO_REMOVE.forEach((header) => headers.delete(header));
  headers.set('host', upstreamHost);
  headers.set('x-forwarded-host', upstreamHost);

  const body = BODYLESS_METHODS.has(request.method)
    ? undefined
    : await request.arrayBuffer();

  return fetch(upstreamUrl, {
    method: request.method,
    headers,
    body,
    redirect: 'manual',
  });
}