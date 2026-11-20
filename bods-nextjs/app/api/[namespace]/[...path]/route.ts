import type { NextRequest } from 'next/server';
import {
  djangoPath,
  forwardToDjango,
  getDjangoNamespace,
  resolveUpstreamHost,
} from '@/lib/django-gateway';

type RouteContext = {
  params: Promise<{ namespace: string; path: string[] }>;
};

async function proxyDjangoRequest(
  request: NextRequest,
  context: RouteContext,
): Promise<Response> {
  const { namespace, path } = await context.params;
  const config = getDjangoNamespace(namespace);

  if (!config) {
    return new Response(null, { status: 404 });
  }

  return forwardToDjango(
    request,
    djangoPath(config.upstreamPrefix, path, request.nextUrl.pathname),
    resolveUpstreamHost(config, request),
  );
}

export const GET = proxyDjangoRequest;
export const HEAD = proxyDjangoRequest;
export const POST = proxyDjangoRequest;
export const PUT = proxyDjangoRequest;
export const PATCH = proxyDjangoRequest;
export const DELETE = proxyDjangoRequest;
export const OPTIONS = proxyDjangoRequest;