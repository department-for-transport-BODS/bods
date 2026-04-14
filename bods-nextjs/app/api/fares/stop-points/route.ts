import http from 'node:http';
import { NextRequest, NextResponse } from 'next/server';

const DJANGO_DATA_ORIGIN = process.env.DJANGO_DATA_INTERNAL_ORIGIN || 'http://127.0.0.1:8000';

const requestFareStops = (revisionId: string) =>
  new Promise<{ statusCode: number; body: string }>((resolve, reject) => {
    const targetUrl = new URL(`/api/app/fare_stops/?revision=${revisionId}`, DJANGO_DATA_ORIGIN);

    const req = http.request(
      {
        hostname: targetUrl.hostname,
        port: targetUrl.port || 80,
        path: `${targetUrl.pathname}${targetUrl.search}`,
        method: 'GET',
        headers: {
          Host: 'data.localhost:8000',
        },
      },
      (response) => {
        const chunks: Buffer[] = [];

        response.on('data', (chunk) => {
          chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
        });

        response.on('end', () => {
          resolve({
            statusCode: response.statusCode ?? 502,
            body: Buffer.concat(chunks).toString('utf-8'),
          });
        });
      },
    );

    req.on('error', reject);
    req.end();
  });

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const revisionId = url.searchParams.get('revisionId');

  if (!revisionId) {
    return NextResponse.json({ error: 'revisionId is required' }, { status: 400 });
  }

  try {
    const djangoResp = await requestFareStops(revisionId);
    const data = JSON.parse(djangoResp.body || '{}');

    if (djangoResp.statusCode < 200 || djangoResp.statusCode >= 300) {
      return NextResponse.json(
        { error: data.error || `Django responded with status ${djangoResp.statusCode}` },
        { status: djangoResp.statusCode },
      );
    }

    return NextResponse.json(data, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}