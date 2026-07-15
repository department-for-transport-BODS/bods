import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../../_utils/session-auth';

function getPublishOrigin(): string {
  const explicitOrigin = process.env.DJANGO_PUBLISH_ORIGIN;
  if (explicitOrigin) {
    return explicitOrigin.replace(/\/$/, '');
  }

  try {
    const parsed = new URL(config.djangoOrigin);
    if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
      parsed.hostname = 'publish.localhost';
      return parsed.toString().replace(/\/$/, '');
    }
  } catch {
    // no-op, fall through to default origin
  }

  return config.djangoOrigin.replace(/\/$/, '');
}

function buildCandidateUrls(orgId: string, pathSuffix: string, query: Record<string, string>): string[] {
  const origins = [getPublishOrigin(), config.djangoOrigin.replace(/\/$/, '')];
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
    const exportCandidates = buildCandidateUrls(orgId, '/dataset/compliance-report/', {});

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

    if (!exportResponse.ok) {
      return NextResponse.json(
        { error: `Django responded with status ${exportResponse.status}` },
        { status: exportResponse.status },
      );
    }

    const contentDisposition = exportResponse.headers.get('Content-Disposition') || '';
    const contentType = exportResponse.headers.get('Content-Type') || 'application/octet-stream';
    const body = exportResponse.body;

    if (!body) {
      return NextResponse.json({ error: 'No file content returned from server' }, { status: 502 });
    }

    return new NextResponse(body, {
      status: 200,
      headers: {
        'Content-Type': contentType,
        'Content-Disposition': contentDisposition,
      },
    });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}