import { NextRequest, NextResponse } from 'next/server';
import { getSessionHeaders, hasSessionCookie } from '@/lib/api-session';
import { proxyDownload } from '../../_utils/download-proxy';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ orgId: string }> },
) {
  const { orgId } = await params;

  if (!hasSessionCookie(request)) {
    return NextResponse.json(
      { error: 'Not authenticated. Please sign in and retry.' },
      { status: 401 },
    );
  }

  try {
    return await proxyDownload(
      getSessionHeaders(request),
      `/org/${orgId}/dataset/data-activity/consumer-feedback/`,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}
