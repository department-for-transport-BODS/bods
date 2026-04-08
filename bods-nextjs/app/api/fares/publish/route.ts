// This API route serves as a bridge to the Django backend for submitting fare datasets for review.
// It handles authentication, forwards the request to Django, and processes the response to work with Next.js routing.
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
    const djangoResp = await fetch(`${DJANGO_ORIGIN}/api/fares/publish/${orgId}/${datasetId}/`, {
      method: 'POST',
      headers: { Authorization: authHeader },
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
