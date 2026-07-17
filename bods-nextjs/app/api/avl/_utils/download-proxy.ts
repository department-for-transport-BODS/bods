import { NextResponse } from 'next/server';
import { config } from '@/config';

function trimTrailingSlash(value: string): string {
  return value.replace(/\/$/, '');
}

function joinOriginAndPath(origin: string, path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${trimTrailingSlash(origin)}${normalizedPath}`;
}

export function getPublishOrigin(): string {
  const explicitOrigin = process.env.DJANGO_PUBLISH_ORIGIN;
  if (explicitOrigin) {
    return trimTrailingSlash(explicitOrigin);
  }

  try {
    const parsed = new URL(config.djangoOrigin);
    if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
      parsed.hostname = 'publish.localhost';
      return trimTrailingSlash(parsed.toString());
    }
  } catch {
    // no-op, fall through to default origin
  }

  return trimTrailingSlash(config.djangoOrigin);
}

export function getDjangoOriginCandidates(): string[] {
  const candidates = [getPublishOrigin(), trimTrailingSlash(config.djangoOrigin)];
  return [...new Set(candidates)];
}

export function toDownloadResponse(response: Response, defaultContentType: string): NextResponse {
  if (!response.ok) {
    return NextResponse.json({ error: `Django responded with status ${response.status}` }, { status: response.status });
  }

  const body = response.body;
  if (!body) {
    return NextResponse.json({ error: 'No file content returned from server' }, { status: 502 });
  }

  const contentDisposition = response.headers.get('Content-Disposition') || '';
  const contentType = response.headers.get('Content-Type') || defaultContentType;

  return new NextResponse(body, {
    status: 200,
    headers: {
      'Content-Type': contentType,
      'Content-Disposition': contentDisposition,
    },
  });
}

export async function proxyDownloadWithPublishFallback(
  sessionHeaders: Headers,
  pathSuffix: string,
  options?: { cache?: RequestCache },
): Promise<NextResponse> {
  const [publishOrigin, djangoOrigin] = getDjangoOriginCandidates();

  let djangoResp = await fetch(joinOriginAndPath(publishOrigin, pathSuffix), {
    method: 'GET',
    headers: sessionHeaders,
    redirect: 'manual',
    cache: options?.cache,
  });

  // Fallback for environments where publish host is not configured and Django is served from one host.
  if (djangoResp.status === 404 && publishOrigin !== djangoOrigin) {
    djangoResp = await fetch(joinOriginAndPath(djangoOrigin, pathSuffix), {
      method: 'GET',
      headers: sessionHeaders,
      redirect: 'manual',
      cache: options?.cache,
    });
  }

  return toDownloadResponse(djangoResp, 'application/zip');
}