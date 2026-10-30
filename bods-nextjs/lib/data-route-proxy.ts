import type { NextRequest } from 'next/server';
import { forwardToDjango, getDjangoNamespace } from '@/lib/django-gateway';

/** Forward a data-host route handler to the same path on Django's data host. */
export async function forwardDataRoute(
  request: NextRequest,
  upstreamPath: string,
): Promise<Response> {
  const config = getDjangoNamespace('data');

  if (!config || !config.upstreamHost) {
    throw new Error('Data Django namespace is not configured');
  }

  return forwardToDjango(request, upstreamPath, config.upstreamHost);
}
