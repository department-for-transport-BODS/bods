import { notFound } from 'next/navigation';
import type { NextRequest } from 'next/server';
import { DJANGO_HOSTS } from '@/config/server';
import { forwardToDjango } from '@/lib/django-gateway';

/**
 * Data catalogue download.
 *
 * Django provides the signed URL through its API; this Next.js route owns the
 * browser-facing redirect.
 */

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest): Promise<Response> {
  const upstream = await forwardToDjango(
    request,
    '/api/catalogue/',
    new URL(DJANGO_HOSTS.www).host,
  );

  if (upstream.status === 404) {
    notFound();
  }

  if (!upstream.ok) {
    return new Response(await upstream.text(), {
      status: upstream.status,
      headers: {
        'Content-Type': upstream.headers.get('content-type') || 'text/plain',
      },
    });
  }

  const { url } = (await upstream.json()) as { url?: unknown };
  if (typeof url !== 'string' || !url.startsWith('https://')) {
    return new Response('Invalid data catalogue download URL.', { status: 502 });
  }

  return Response.redirect(url, 302);
}
