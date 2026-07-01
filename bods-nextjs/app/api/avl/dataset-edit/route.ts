import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  try {
    const djangoResp = await fetch(`${config.djangoOrigin}/api/avl/dataset-edit/${orgId}/${datasetId}/`, {
      method: 'GET',
      headers: {
        cookie: request.headers.get('cookie') || '',
      },
    });

    const data = await djangoResp.json().catch(() => ({}));

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: (data as { error?: string }).error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  const outgoing = new FormData();
  const incoming = await request.formData();
  for (const [key, value] of incoming.entries()) {
    if (value instanceof File) {
      outgoing.set(key, value, value.name);
    } else {
      outgoing.set(key, value);
    }
  }

  try {
    const djangoResp = await fetch(`${config.djangoOrigin}/api/avl/dataset-edit/${orgId}/${datasetId}/save/`, {
      method: 'POST',
      body: outgoing,
      headers: {
        cookie: request.headers.get('cookie') || '',
      },
      redirect: 'manual',
    });

    const data = (await djangoResp.json().catch(() => ({}))) as {
      redirect?: string;
      error?: string;
      field_errors?: Record<string, string[] | string>;
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
