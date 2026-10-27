import type { NextRequest } from 'next/server';
import { forwardToDjango, getDjangoNamespace, resolveUpstreamHost } from '@/lib/django-gateway';

export async function forwardPublishRoute(
  request: NextRequest,
  upstreamPath: string,
): Promise<Response> {
  const config = getDjangoNamespace('publish');

  if (!config) {
    throw new Error('Publish Django namespace is not configured');
  }

  return forwardToDjango(request, upstreamPath, resolveUpstreamHost(config, request));
}
