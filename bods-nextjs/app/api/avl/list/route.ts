import { NextRequest, NextResponse } from 'next/server';
import { config } from '@/config';
import { getSessionHeaders, hasSessionCookie } from '../_utils/session-auth';

type AvlListItem = {
  id: number;
  name: string;
  status: string;
  has_live_revision?: boolean;
  short_description: string;
  avl_feed_last_checked: string | null;
  modified: string | null;
};

export async function GET(request: NextRequest) {
  const url = new URL(request.url);
  const orgId = url.searchParams.get('orgId');
  const tab = url.searchParams.get('tab') || 'active';
  const sortBy = url.searchParams.get('sort_by') || 'modified';
  const order = url.searchParams.get('order') || 'desc';
  const page = url.searchParams.get('page') || '1';
  const parsedPage = Number.parseInt(page, 10);
  const requestedPage = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;

  if (!orgId) {
    return NextResponse.json({ error: 'orgId is required' }, { status: 400 });
  }

  if (!hasSessionCookie(request)) {
    return NextResponse.json({ error: 'Not authenticated. Please sign in and retry.' }, { status: 401 });
  }

  try {
    if (tab === 'draft') {
      const draftResults = await loadDraftFeeds(orgId, request);
      const sortedDraftResults = sortResults(draftResults, sortBy, order);

      const pageSize = 10;
      const count = sortedDraftResults.length;
      const totalPages = Math.max(1, Math.ceil(count / pageSize));
      const currentPage = Math.min(requestedPage, totalPages);
      const start = (currentPage - 1) * pageSize;
      const results = sortedDraftResults.slice(start, start + pageSize);

      return NextResponse.json(
        {
          count,
          page: currentPage,
          pageSize,
          totalPages,
          hasNext: currentPage < totalPages,
          hasPrevious: currentPage > 1,
          results,
        },
        { status: 200 },
      );
    }

    const djangoResp = await fetch(
      `${config.djangoOrigin}/api/avl/list/${orgId}/?tab=${encodeURIComponent(tab)}&sort_by=${encodeURIComponent(sortBy)}&order=${encodeURIComponent(order)}`,
      {
        method: 'GET',
        headers: getSessionHeaders(request),
      },
    );

    const data = await djangoResp.json().catch(() => ({}));

    if (!djangoResp.ok) {
      return NextResponse.json(
        { error: (data as { error?: string }).error || `Django responded with status ${djangoResp.status}` },
        { status: djangoResp.status },
      );
    }

    const payload = data as { count?: number; results?: unknown[] };
    const allResults = Array.isArray(payload.results) ? payload.results : [];

    const pageSize = 10;
    const count = typeof payload.count === 'number' ? payload.count : allResults.length;
    const totalPages = Math.max(1, Math.ceil(count / pageSize));
    const currentPage = Math.min(requestedPage, totalPages);
    const start = (currentPage - 1) * pageSize;
    const results = allResults.slice(start, start + pageSize);

    return NextResponse.json(
      {
        count,
        page: currentPage,
        pageSize,
        totalPages,
        hasNext: currentPage < totalPages,
        hasPrevious: currentPage > 1,
        results,
      },
      { status: 200 },
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to reach Django: ${message}` }, { status: 502 });
  }
}

async function loadDraftFeeds(orgId: string, request: NextRequest): Promise<AvlListItem[]> {
  const publishOrigin = config.djangoOrigin.replace('://localhost', '://publish.localhost');
  const draftPageCandidates = [
    `${config.djangoOrigin}/org/${orgId}/dataset/avl/?tab=draft`,
    `${config.djangoOrigin}/publish/org/${orgId}/dataset/avl/?tab=draft`,
    `${publishOrigin}/org/${orgId}/dataset/avl/?tab=draft`,
    `${publishOrigin}/publish/org/${orgId}/dataset/avl/?tab=draft`,
  ];

  let html = '';
  let datasetIds: number[] = [];

  for (const candidateUrl of draftPageCandidates) {
    const draftHtmlResp = await fetch(candidateUrl, {
      method: 'GET',
      headers: getSessionHeaders(request),
    });

    if (!draftHtmlResp.ok) {
      continue;
    }

    html = await draftHtmlResp.text();

    const idsFromLinks = Array.from(html.matchAll(/\/dataset\/avl\/(\d+)(?:\/|\?|"|')/g), (match) => Number.parseInt(match[1], 10));
    const idsFromCells = Array.from(html.matchAll(/<td[^>]*class="govuk-table__cell"[^>]*>\s*(\d+)\s*<\/td>/g), (match) => Number.parseInt(match[1], 10));

    datasetIds = [...new Set([...idsFromLinks, ...idsFromCells].filter((id) => !Number.isNaN(id)))];
    if (datasetIds.length > 0) {
      break;
    }
  }

  if (datasetIds.length === 0) {
    return [];
  }

  const draftRows: Array<AvlListItem | null> = await Promise.all(
    datasetIds.map(async (datasetId) => {
      const reviewResp = await fetch(
        `${config.djangoOrigin}/api/avl/review-status/${orgId}/${datasetId}/`,
        {
          method: 'GET',
          headers: getSessionHeaders(request),
        },
      );

      if (!reviewResp.ok) {
        return null;
      }

      const data = (await reviewResp.json().catch(() => ({}))) as {
        datasetId?: number;
        name?: string;
        status?: string;
        hasLiveRevision?: boolean;
        shortDescription?: string;
        lastModified?: string;
      };

      return {
        id: data.datasetId ?? datasetId,
        name: data.name || '',
        status: data.status || 'draft',
        has_live_revision: Boolean(data.hasLiveRevision),
        short_description: data.shortDescription || '',
        avl_feed_last_checked: null,
        modified: data.lastModified || null,
      } as AvlListItem;
    }),
  );

  return draftRows.filter((row): row is AvlListItem => row !== null);
}

function sortResults(results: AvlListItem[], sortBy: string, order: string): AvlListItem[] {
  const direction = order === 'asc' ? 1 : -1;
  const sorted = [...results].sort((a, b) => {
    switch (sortBy) {
      case 'status':
        return a.status.localeCompare(b.status);
      case 'name':
        return a.name.localeCompare(b.name);
      case 'id':
        return a.id - b.id;
      case 'avl_feed_last_checked': {
        const aTime = a.avl_feed_last_checked ? new Date(a.avl_feed_last_checked).getTime() : 0;
        const bTime = b.avl_feed_last_checked ? new Date(b.avl_feed_last_checked).getTime() : 0;
        return aTime - bTime;
      }
      case 'short_description':
        return a.short_description.localeCompare(b.short_description);
      case 'modified':
      default: {
        const aTime = a.modified ? new Date(a.modified).getTime() : 0;
        const bTime = b.modified ? new Date(b.modified).getTime() : 0;
        return aTime - bTime;
      }
    }
  });

  return direction === 1 ? sorted : sorted.reverse();
}
