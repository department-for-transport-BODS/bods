import type { NextRequest } from 'next/server';
import { forwardDataRoute } from '@/lib/data-route-proxy';
import { isValidAuthIds } from '@/lib/local-authority';

/**
 * Builds the GET/HEAD handler for a Local Transport Authority CSV export. Django
 * generates the file, so the response (body and Content-Disposition) is passed through.
 * Django 500s on a missing or malformed `auth_ids`; those requests 404 here instead of
 * being proxied.
 */
export function localAuthorityExportHandler(upstreamPath: string) {
  return async function handler(request: NextRequest): Promise<Response> {
    if (!isValidAuthIds(request.nextUrl.searchParams.get('auth_ids'))) {
      return new Response(null, { status: 404 });
    }

    return forwardDataRoute(request, upstreamPath);
  };
}
