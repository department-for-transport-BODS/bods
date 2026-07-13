import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../_utils/session-auth';

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    const djangoResp = await fetch(`${config.djangoOrigin}/api/avl/delete/${orgId}/${datasetId}/`, {
      method: 'POST',
      headers: getSessionHeaders(request, { includeCsrf: true }),
      redirect: 'manual',
    });

    const data = (await djangoResp.json().catch(() => ({}))) as {
      redirect?: string;
      error?: string;
    };

    if (!djangoResp.ok) {
      return NextResponse.json(
        {
          error: data.error || `Django responded with status ${djangoResp.status}`,
        },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(
      {
        redirect: toNextJsPath(data.redirect || ''),
      },
      { status: 200 },
    );
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
    const parsed = new URL(djangoUrl, 'http://placeholder');
    if (parsed.pathname.startsWith('/publish/')) {
      return `${parsed.pathname}${parsed.search}`;
    }
    if (parsed.pathname.startsWith('/org/')) {
      return `/publish${parsed.pathname}${parsed.search}`;
    }
    return `${parsed.pathname}${parsed.search}`;
  } catch {
    if (djangoUrl.startsWith('/publish/')) {
      return djangoUrl;
    }
    if (djangoUrl.startsWith('/org/')) {
      return `/publish${djangoUrl}`;
    }
    return djangoUrl;
  }
}
