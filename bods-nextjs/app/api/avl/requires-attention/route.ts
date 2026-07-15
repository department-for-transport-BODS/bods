import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../_utils/session-auth';

export const dynamic = 'force-dynamic';
export const revalidate = 0;

interface AttentionSummary {
  available: boolean;
  servicesRequiringAttention: number | null;
  totalInScopeInSeasonServices: number | null;
  percentage: number;
  detailUrl: string | null;
}

interface AttentionRow {
  licenceNumber: string;
  serviceCode: string;
  lineNumber: string;
}

interface AttentionResponse {
  summary: AttentionSummary;
  rows: AttentionRow[];
  pagination: {
    currentPage: number;
    totalPages: number;
  };
  query: string;
  exportUrl: string | null;
  noResults: boolean;
}

function buildExportProxyUrl(orgId: string): string {
  const url = new URL('/api/avl/requires-attention/export', 'http://localhost');
  url.searchParams.set('orgId', orgId);
  return `${url.pathname}${url.search}`;
}

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const q = (url.searchParams.get('q') || '').trim();
  const summaryOnly = url.searchParams.get('summaryOnly') === '1';
  const pageParam = url.searchParams.get('page') || '1';
  const parsedPage = Number.parseInt(pageParam, 10);
  const requestedPage = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;

  if (!orgId) {
    return NextResponse.json({ error: 'orgId is required' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    const djangoResp = await fetch(
      `${config.djangoOrigin}/api/avl/requires-attention/${orgId}/?q=${encodeURIComponent(q)}&page=${requestedPage}${summaryOnly ? '&summaryOnly=1' : ''}`,
      {
        method: 'GET',
        headers: getSessionHeaders(request),
        cache: 'no-store',
      },
    );

    const payload = (await djangoResp.json().catch(() => ({}))) as AttentionResponse & { error?: string };

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: payload.error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    return NextResponse.json(
      {
        ...payload,
        exportUrl: summaryOnly ? null : buildExportProxyUrl(orgId),
      },
      { status: 200 },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to load attention data: ${message}` }, { status: 502 });
  }
}
