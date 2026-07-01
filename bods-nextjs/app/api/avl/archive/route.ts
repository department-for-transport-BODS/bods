import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';

const DEACTIVATE_SUBMIT_BODY = 'submit=submit';

export async function POST(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const datasetId = url.searchParams.get('datasetId');

  if (!orgId || !datasetId) {
    return NextResponse.json({ error: 'orgId and datasetId are required' }, { status: 400 });
  }

  const cookieHeader = request.headers.get('cookie') || '';
  const csrfHeader = request.headers.get('x-csrftoken') || request.headers.get('X-CSRFToken') || '';

  try {
    const publishOrigin = getPublishOrigin();
    let djangoResp = await postDeactivate(
      `${publishOrigin}/org/${orgId}/dataset/avl/${datasetId}/deactivate/`,
      cookieHeader,
      csrfHeader,
    );

    // Fallback for environments where publish host isn't configured and Django is served from one host.
    if (djangoResp.status === 404 && publishOrigin !== config.djangoOrigin) {
      djangoResp = await postDeactivate(
        `${config.djangoOrigin}/org/${orgId}/dataset/avl/${datasetId}/deactivate/`,
        cookieHeader,
        csrfHeader,
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

function postDeactivate(url: string, cookieHeader: string, csrfHeader: string): Promise<Response> {
  return fetch(url, {
    method: 'POST',
    headers: {
      cookie: cookieHeader,
      'Content-Type': 'application/x-www-form-urlencoded',
      ...(csrfHeader ? { 'X-CSRFToken': csrfHeader } : {}),
    },
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
