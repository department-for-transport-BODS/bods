import type { NextRequest } from 'next/server';
import { DJANGO_HOSTS, serverConfig } from '@/config/server';
import { bodsAreaFromHostname, hostnameFromHeaders } from '@/config/hosts';

const BODYLESS_METHODS = new Set(['GET', 'HEAD']);
const REQUEST_HEADERS_TO_REMOVE = [
  'content-length',
  'host',
  'x-forwarded-host',
];

const DJANGO_NAMESPACES = {
  auth: {
    upstreamPrefix: '/api/auth/',
    // Session auth is mounted on every Django service host, so the upstream is
    // resolved per request from the browser-facing subdomain.
    upstreamHost: null,
  },
  data: {
    upstreamPrefix: '/api/',
    upstreamHost: new URL(DJANGO_HOSTS.data).host,
  },
  publish: {
    upstreamPrefix: '/api/',
    upstreamHost: new URL(DJANGO_HOSTS.publish).host,
  },
} as const;

type DjangoNamespaceConfig = (typeof DJANGO_NAMESPACES)[keyof typeof DJANGO_NAMESPACES];

export function getDjangoNamespace(namespace: string): DjangoNamespaceConfig | null {
  return DJANGO_NAMESPACES[namespace as keyof typeof DJANGO_NAMESPACES] ?? null;
}

// Session auth is served by every service host - forward to the respective Django host
// so the session cookie and Django's CSRF origin check stay aligned with the host the user is on.
export function resolveUpstreamHost(
  config: DjangoNamespaceConfig,
  request: NextRequest,
): string {
  if (config.upstreamHost) {
    return config.upstreamHost;
  }

  const hostname = hostnameFromHeaders(
    request.headers.get('host'),
    request.headers.get('x-forwarded-host'),
  );
  return new URL(DJANGO_HOSTS[bodsAreaFromHostname(hostname)]).host;
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