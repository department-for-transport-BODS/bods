import { notFound } from 'next/navigation';
import type { NextRequest } from 'next/server';
import { DJANGO_HOSTS } from '@/config/server';
import { forwardToDjango } from '@/lib/django-gateway';

/**
 * Data catalogue download.
 *
 * Source: transit_odp/browse/views/data_catalogue.py - DownloadDataCatalogueView
 * Django either streams the latest data catalogue archive (with its
 * Content-Disposition) or, when `is_direct_s3_url_active` is on, redirects to a
 * signed S3/CDN URL. Both are passed straight through to the browser.
 */

export const dynamic = 'force-dynamic';

const NO_BODY_STATUSES = new Set([204, 205, 304]);
// fetch() has already decoded the body, so these no longer describe it.
const DECODED_BODY_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding'];

export async function GET(request: NextRequest): Promise<Response> {
  const upstream = await forwardToDjango(
    request,
    '/catalogue/',
    new URL(DJANGO_HOSTS.data).host,
  );

  // Django raises Http404 when no data catalogue archive has been uploaded yet.
  if (upstream.status === 404) {
    notFound();
  }

  const headers = new Headers(upstream.headers);
  if (upstream.headers.has('content-encoding')) {
    DECODED_BODY_HEADERS.forEach((header) => headers.delete(header));
  }

  const isRedirect = upstream.status >= 300 && upstream.status < 400;
  const body = isRedirect || NO_BODY_STATUSES.has(upstream.status) ? null : upstream.body;

  return new Response(body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}
