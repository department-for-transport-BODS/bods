import { NextRequest, NextResponse } from 'next/server';
import { getSessionHeaders, hasSessionCookie } from '@/lib/api-session';
import { isNumericId } from '@/lib/utils/numeric-id';
import { serverConfig } from '@/config/server';
import { toDownloadResponse } from '../../_utils/download-proxy';

export async function GET(request: NextRequest) {
  const orgId = new URL(request.url).searchParams.get('orgId');

  if (!isNumericId(orgId)) {
    return NextResponse.json({ error: 'orgId must be numeric' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json(
      { error: 'Not authenticated. Please sign in and retry.' },
      { status: 401 },
    );
  }

  try {
    const response = await fetch(
      `${serverConfig.djangoInternalOrigin}/org/${orgId}/dataset/timetable/compliance-report/`,
      {
        method: 'GET',
        headers: getSessionHeaders(request),
        cache: 'no-store',
        redirect: 'manual',
      },
    );

    return toDownloadResponse(response, 'application/octet-stream');
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}
