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
    const djangoResp = await fetch(`${DJANGO_ORIGIN}/api/fares/deactivate/${orgId}/${datasetId}/`, {
      method: 'POST',
      headers: { Authorization: authHeader },
    });

    const data = (await djangoResp.json().catch(() => ({}))) as {
      redirect?: string;
      error?: string;
      deactivated?: boolean;
      dataset_name?: string;
    };

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: data.error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(
      {
        redirect: data.redirect || `/publish/org/${orgId}/dataset/fares`,
        deactivated: true,
        dataset_name: data.dataset_name || '',
      },
      { status: 200 },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}
