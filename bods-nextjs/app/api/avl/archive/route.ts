import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../_utils/session-auth';

const DEACTIVATE_SUBMIT_BODY = 'submit=submit';

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  const sessionHeaders = getSessionHeaders(request, { includeCsrf: true });

  try {
    const publishOrigin = getPublishOrigin();
    let djangoResp = await postDeactivate(
      `${publishOrigin}/org/${orgId}/dataset/avl/${datasetId}/deactivate/`,
      sessionHeaders,
    );

    // Fallback for environments where publish host isn't configured and Django is served from one host.
    if (djangoResp.status === 404 && publishOrigin !== config.djangoOrigin) {
      djangoResp = await postDeactivate(
        `${config.djangoOrigin}/org/${orgId}/dataset/avl/${datasetId}/deactivate/`,
        sessionHeaders,
      );
    }

    const location = djangoResp.headers.get('location') || '';

    if (djangoResp.status >= 300 && djangoResp.status < 400) {
      return NextResponse.json({ redirect: toNextJsPath(location, orgId, datasetId) }, { status: 200 });
    }

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    // Defensive fallback for deployments where redirects are auto-followed upstream.
    return NextResponse.json(
      { redirect: `/publish/org/${orgId}/dataset/avl/${datasetId}/archive/success` },
      { status: 200 },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}

function postDeactivate(
  url: string,
  sessionHeaders: Headers,
): Promise<Response> {
  const headers = new Headers(sessionHeaders);
  headers.set('Content-Type', 'application/x-www-form-urlencoded');

  return fetch(url, {
    method: 'POST',
    headers,
    body: DEACTIVATE_SUBMIT_BODY,
    redirect: 'manual',
  });
}

function getPublishOrigin(): string {
  const explicitOrigin = process.env.DJANGO_PUBLISH_ORIGIN;
  if (explicitOrigin) {
    return explicitOrigin;
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

  return config.djangoOrigin;
}

function toNextJsPath(djangoUrl: string, orgId: string, datasetId: string): string {
  if (!djangoUrl) {
    return `/publish/org/${orgId}/dataset/avl/${datasetId}/archive/success`;
  }

  try {
    const parsed = new URL(djangoUrl, 'http://placeholder');
    let pathname = parsed.pathname;

    if (pathname.startsWith('/org/')) {
      pathname = `/publish${pathname}`;
    }

    pathname = pathname.replace('/deactivate/', '/archive/');

    return `${pathname}${parsed.search}`;
  } catch {
    const withPublishPrefix = djangoUrl.startsWith('/org/') ? `/publish${djangoUrl}` : djangoUrl;
    return withPublishPrefix.replace('/deactivate/', '/archive/');
  }
}
