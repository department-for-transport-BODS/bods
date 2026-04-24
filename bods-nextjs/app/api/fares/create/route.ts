//forwards form data from the frontend to Django, including file uploads, 
// and handles authentication via Bearer tokens
// The route also processes Django's response, returning any errors or redirect URLs back to the frontend in a Next.js-friendly format.
import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';

export async function POST(request: NextRequest) {
  const orgId = new URL(request.url).searchParams.get('orgId');
  if (!orgId) {
    return NextResponse.json({ error: 'orgId is required' }, { status: 400 });
  }

  const authHeader = request.headers.get('authorization') || '';
  if (!authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  const createUrl = `${config.djangoOrigin}/api/fares/create/${orgId}/`;
  const incoming = await request.formData();

  const outgoing = new FormData();
  for (const [key, value] of incoming.entries()) {
    if (value instanceof File) {
      outgoing.set(key, value, value.name);
    } else {
      outgoing.set(key, value);
    }
  }

  try {
    const djangoResp = await fetch(createUrl, {
      method: 'POST',
      body: outgoing,
      headers: {
        Authorization: authHeader,
      },
      redirect: 'manual',
    });

    const data = (await djangoResp.json().catch(() => ({}))) as {
      redirect?: string;
      error?: string;
      field_errors?: Record<string, string[]>;
    };

    if (!djangoResp.ok) {
      return NextResponse.json(
        {
          error: data.error || `Django responded with status ${djangoResp.status}`,
          fieldErrors: data.field_errors,
        },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json({ redirect: toNextJsPath(data.redirect || '') }, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}

function toNextJsPath(djangoUrl: string): string {
  if (!djangoUrl) {
    return '';
  }
  try {
    const url = new URL(djangoUrl, 'http://placeholder');
    const path = url.pathname;
    if (path.startsWith('/org/')) {
      return `/publish${path}`;
    }
    return `/publish${path}`;
  } catch {
    if (djangoUrl.startsWith('/org/')) {
      return `/publish${djangoUrl}`;
    }
    return djangoUrl;
  }
}
