import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../../_utils/session-auth';

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

export async function GET(request: NextRequest, { params }: { params: Promise<{ orgId: string }> }) {
  const { orgId } = await params;

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  const sessionHeaders = getSessionHeaders(request);

  try {
    const publishOrigin = getPublishOrigin();
    let djangoResp = await fetch(`${publishOrigin}/org/${orgId}/dataset/data-activity/consumer-interactions/`, {
      method: 'GET',
      headers: sessionHeaders,
      redirect: 'manual',
    });

    // Fallback for environments where publish host isn't configured and Django is served from one host.
    if (djangoResp.status === 404 && publishOrigin !== config.djangoOrigin) {
      djangoResp = await fetch(`${config.djangoOrigin}/org/${orgId}/dataset/data-activity/consumer-interactions/`, {
        method: 'GET',
        headers: sessionHeaders,
        redirect: 'manual',
      });
    }

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    const contentDisposition = djangoResp.headers.get('Content-Disposition') || '';
    const contentType = djangoResp.headers.get('Content-Type') || 'application/zip';
    const body = djangoResp.body;

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
