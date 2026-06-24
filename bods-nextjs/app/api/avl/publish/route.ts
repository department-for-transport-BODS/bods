import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');
  const isUpdate = url.searchParams.get('isUpdate') === 'true';

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  const authHeader = request.headers.get('authorization') || '';
  if (!authHeader.startsWith('Bearer ')) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  const publishPath = isUpdate
    ? `/api/avl/publish-update/${orgId}/${datasetId}/`
    : `/api/avl/publish/${orgId}/${datasetId}/`;

  try {
    const djangoResp = await fetch(`${config.djangoOrigin}${publishPath}`, {
      method: 'POST',
      headers: {
        Authorization: authHeader,
      },
    });

    const data = await djangoResp.json().catch(() => ({}));

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: data.error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}
