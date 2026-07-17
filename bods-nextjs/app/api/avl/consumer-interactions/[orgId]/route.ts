import { NextRequest, NextResponse } from 'next/server';
import { proxyDownloadWithPublishFallback } from '../../_utils/download-proxy';
import { getSessionHeaders, hasSessionCookie } from '../../_utils/session-auth';

export async function GET(request: NextRequest, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  const sessionHeaders = getSessionHeaders(request);

  try {
    return await proxyDownloadWithPublishFallback(
      sessionHeaders,
      `/org/${orgId}/dataset/data-activity/consumer-interactions/`,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}
