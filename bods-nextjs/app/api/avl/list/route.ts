import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const tab = url.searchParams.get('tab') || 'active';

  if (!orgId) {
    return NextResponse.json({ error: 'orgId is required' }, { status: 400 });
  }

  const authHeader = request.headers.get('authorization') || '';
  if (!authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    const djangoResp = await fetch(
      `${config.djangoOrigin}/api/avl/list/${orgId}/?tab=${encodeURIComponent(tab)}`,
      {
        method: 'GET',
        headers: {
          Authorization: authHeader,
        },
      },
    );

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
