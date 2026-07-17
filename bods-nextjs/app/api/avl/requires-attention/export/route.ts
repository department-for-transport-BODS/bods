import { NextRequest, NextResponse } from 'next/server';
import { getDjangoOriginCandidates, toDownloadResponse } from '../../_utils/download-proxy';
import { getSessionHeaders, hasSessionCookie } from '../../_utils/session-auth';

function buildCandidateUrls(orgId: string, pathSuffix: string, query: Record<string, string>): string[] {
  const origins = getDjangoOriginCandidates();
  const prefixes = ['', '/publish'];
  const urls: string[] = [];

  for (const origin of origins) {
    for (const prefix of prefixes) {
      const url = new URL(`${origin}${prefix}/org/${orgId}${pathSuffix}`);
      Object.entries(query).forEach(([key, value]) => {
        if (value) {
          url.searchParams.set(key, value);
        }
      });
      urls.push(url.toString());
    }
  }

  return [...new Set(urls)];
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');

  if (!orgId) {
    return NextResponse.json({ error: 'orgId is required' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    const sessionHeaders = getSessionHeaders(request);
    const exportCandidates = buildCandidateUrls(orgId, '/dataset/timetable/compliance-report/', {});

    let exportResponse = await fetch(exportCandidates[0], {
      method: 'GET',
      headers: sessionHeaders,
      cache: 'no-store',
      redirect: 'manual',
    });

    if (!exportResponse.ok && exportCandidates.length > 1) {
      for (const candidate of exportCandidates.slice(1)) {
        exportResponse = await fetch(candidate, {
          method: 'GET',
          headers: sessionHeaders,
          cache: 'no-store',
          redirect: 'manual',
        });

        if (exportResponse.ok) {
          break;
        }
      }
    }

    return toDownloadResponse(exportResponse, 'application/octet-stream');
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}