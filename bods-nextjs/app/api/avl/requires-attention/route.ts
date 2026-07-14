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
    const sessionHeaders = getSessionHeaders(request);
    const summary = await loadAttentionSummary(orgId, sessionHeaders);

    if (summaryOnly) {
      const response: AttentionResponse = {
        summary,
        rows: [],
        pagination: {
          currentPage: 1,
          totalPages: 1,
        },
        query: '',
        exportUrl: null,
        noResults: false,
      };

      return NextResponse.json(response, { status: 200 });
    }

    const details = await loadAttentionDetails(orgId, q, requestedPage, sessionHeaders);

    const response: AttentionResponse = {
      summary,
      rows: details.rows,
      pagination: details.pagination,
      query: q,
      exportUrl: details.exportUrl,
      noResults: details.noResults,
    };

    return NextResponse.json(response, { status: 200 });
  } catch (err) {
    const message = err instanceof Error ? err.message : String(err);
    return NextResponse.json({ error: `Failed to load attention data: ${message}` }, { status: 502 });
  }
}

async function loadAttentionSummary(orgId: string, headers: Headers): Promise<AttentionSummary> {
  const listCandidates = buildCandidateUrls(orgId, '/dataset/avl/', { tab: 'active' });
  const { html, url } = await fetchFirstHtml(listCandidates, headers);

  const marker = 'Total service codes that require attention';
  const markerIndex = html.indexOf(marker);

  if (markerIndex < 0) {
    return {
      available: false,
      servicesRequiringAttention: null,
      totalInScopeInSeasonServices: null,
      percentage: 0,
      detailUrl: null,
    };
  }

  const beforeMarker = html.slice(Math.max(0, markerIndex - 2000), markerIndex);
  const afterMarker = html.slice(markerIndex, markerIndex + 800);

  const topValue = getLastMatch(beforeMarker, /review-stat__top"[^>]*>\s*([^<]+)\s*<\/span>/g);
  const bottomValue = getLastMatch(beforeMarker, /review-stat__bottom"[^>]*>\s*\/\s*([^<]+)\s*<\/span>/g);

  const servicesRequiringAttention = parseInteger(topValue);
  const totalInScopeInSeasonServices = parseInteger(bottomValue);

  const href = getFirstMatch(afterMarker, /<a[^>]*class="review-stat__link"[^>]*href\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))/i);
  const detailUrl = resolveHref(href, url);

  const percentage =
    servicesRequiringAttention != null &&
    totalInScopeInSeasonServices != null &&
    totalInScopeInSeasonServices > 0
      ? Math.round((100 * servicesRequiringAttention) / totalInScopeInSeasonServices)
      : 0;

  return {
    available: true,
    servicesRequiringAttention,
    totalInScopeInSeasonServices,
    percentage,
    detailUrl,
  };
}

async function loadAttentionDetails(orgId: string, q: string, page: number, headers: Headers) {
  const detailsCandidates = buildCandidateUrls(orgId, '/dataset/avl/attention/', {
    q,
    page: String(page),
  });

  const { html, url } = await fetchFirstHtml(detailsCandidates, headers);

  const tbodyMatch = html.match(/<tbody[^>]*>([\s\S]*?)<\/tbody>/i);
  const tbody = tbodyMatch ? tbodyMatch[1] : '';

  const rows: AttentionRow[] = [];
  const rowMatches = tbody.matchAll(/<tr[^>]*>([\s\S]*?)<\/tr>/gi);

  for (const rowMatch of rowMatches) {
    const cells = Array.from(rowMatch[1].matchAll(/<td[^>]*>([\s\S]*?)<\/td>/gi)).map((cellMatch) =>
      normalizeText(cellMatch[1]),
    );

    if (cells.length >= 3) {
      rows.push({
        licenceNumber: cells[0],
        serviceCode: cells[1],
        lineNumber: cells[2],
      });
    }
  }

  const currentPageFromHtml = getFirstMatch(
    html,
    /govuk-pagination__item--current[\s\S]*?<a[^>]*>\s*(\d+)\s*<\/a>/i,
  );
  const currentPage = parseInteger(currentPageFromHtml) ?? page;

  const pageNumbers = Array.from(html.matchAll(/[?&]page=(\d+)/g), (match) => Number.parseInt(match[1], 10)).filter(
    (value) => !Number.isNaN(value),
  );
  const totalPages = Math.max(currentPage, pageNumbers.length > 0 ? Math.max(...pageNumbers) : 1);

  const exportHref = getFirstMatch(
    html,
    /<a[^>]*href\s*=\s*(?:"([^"]+)"|'([^']+)'|([^\s>]+))[^>]*>\s*Download detailed export\s*<\/a>/i,
  );

  return {
    rows,
    pagination: {
      currentPage,
      totalPages,
    },
    exportUrl: resolveHref(exportHref, url),
    noResults: html.includes('Sorry, no results found for your search') || rows.length === 0,
  };
}

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

function buildCandidateUrls(
  orgId: string,
  pathSuffix: string,
  query: Record<string, string>,
): string[] {
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

async function fetchFirstHtml(candidates: string[], headers: Headers): Promise<{ html: string; url: string }> {
  let lastError: string | null = null;

  for (const candidate of candidates) {
    const response = await fetch(candidate, {
      method: 'GET',
      headers,
      cache: 'no-store',
      redirect: 'manual',
    });

    if (response.ok) {
      return { html: await response.text(), url: candidate };
    }

    if (response.status !== 404) {
      lastError = `status ${response.status} from ${candidate}`;
    }
  }

  throw new Error(lastError || 'Unable to load page from Django');
}

function parseInteger(value: string | null): number | null {
  if (!value) {
    return null;
  }

  const match = value.match(/\d+/g);
  if (!match) {
    return null;
  }

  const parsed = Number.parseInt(match.join(''), 10);
  return Number.isNaN(parsed) ? null : parsed;
}

function getLastMatch(input: string, regex: RegExp): string | null {
  const matches = Array.from(input.matchAll(regex));
  if (matches.length === 0) {
    return null;
  }

  const last = matches[matches.length - 1];
  return (last[1] || '').trim() || null;
}

function getFirstMatch(input: string, regex: RegExp): string | null {
  const match = input.match(regex);
  if (!match) {
    return null;
  }

  return (match[1] || match[2] || match[3] || '').trim() || null;
}

function resolveHref(href: string | null, baseUrl: string): string | null {
  if (!href) {
    return null;
  }

  try {
    return new URL(href, baseUrl).toString();
  } catch {
    return href;
  }
}

function normalizeText(value: string): string {
  return decodeHtml(stripTags(value)).replace(/\s+/g, ' ').trim();
}

function stripTags(input: string): string {
  return input.replace(/<[^>]*>/g, ' ');
}

function decodeHtml(input: string): string {
  return input
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&#39;/g, "'")
    .replace(/&quot;/g, '"');
}
