import { notFound } from 'next/navigation';
import type { NextRequest } from 'next/server';
import { DJANGO_HOSTS } from '@/config/server';
import { forwardToDjango } from '@/lib/django-gateway';

const NO_BODY_STATUSES = new Set([204, 205, 304]);
// fetch() has already decoded the body, so these no longer describe it.
const DECODED_BODY_HEADERS = ['content-encoding', 'content-length', 'transfer-encoding'];

/**
 * Forward a data-host file download to Django and pass the answer straight back.
 *
 * Django's download views either stream the archive (with its Content-Disposition)
 * or, when `is_direct_s3_url_active` is on, redirect to a signed S3/CDN URL. Both
 * are returned unchanged (redirects are not followed). Django raises Http404 when
 * there is no archive to serve, which becomes the site 404 page.
 */
export async function forwardDataFile(
  request: NextRequest,
  upstreamPath: string,
): Promise<Response> {
  const upstream = await forwardToDjango(request, upstreamPath, new URL(DJANGO_HOSTS.data).host);

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
