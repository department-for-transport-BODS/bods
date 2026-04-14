import { NextRequest, NextResponse } from 'next/server';

const DJANGO_ORIGIN = process.env.DJANGO_INTERNAL_ORIGIN || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  const authHeader = request.headers.get('authorization') || '';
  if (!authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    const djangoResp = await fetch(`${DJANGO_ORIGIN}/api/fares/delete/${orgId}/${datasetId}/`, {
      method: 'POST',
      headers: { Authorization: authHeader },
    });

    const data = (await djangoResp.json().catch(() => ({}))) as {
      redirect?: string;
      error?: string;
      deleted?: boolean;
    };

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: data.error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(
      {
        redirect: toNextJsPath(data.redirect || ''),
        deleted: Boolean(data.deleted),
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
