import { NextResponse } from 'next/server';
import { config } from '@/runtime-config';

function djangoUrl(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;
  return `${config.djangoInternalOrigin.replace(/\/$/, '')}${normalizedPath}`;
}

export function toDownloadResponse(
  response: Response,
  defaultContentType: string,
): NextResponse {
  if (!response.ok) {
    return NextResponse.json(
      { error: `Django responded with status ${response.status}` },
      { status: response.status },
    );
  }

  if (!response.body) {
    return NextResponse.json(
      { error: 'No file content returned from server' },
      { status: 502 },
    );
  }

  return new NextResponse(response.body, {
    status: 200,
    headers: {
      'Content-Type': response.headers.get('Content-Type') || defaultContentType,
      'Content-Disposition': response.headers.get('Content-Disposition') || '',
    },
  });
}

export async function proxyDownload(
  sessionHeaders: Headers,
  path: string,
  options?: { cache?: RequestCache },
): Promise<NextResponse> {
  const response = await fetch(djangoUrl(path), {
    method: 'GET',
    headers: sessionHeaders,
    redirect: 'manual',
    cache: options?.cache,
  });

  return toDownloadResponse(response, 'application/zip');
}
