/** @jest-environment node */

import { dataPath } from '@/config/client';
import DatasetDetailPage, { generateMetadata } from './page';

jest.mock('next/navigation', () => ({
  notFound: () => {
    throw new Error('NEXT_HTTP_ERROR_FALLBACK;404');
  },
}));

jest.mock('next/server', () => ({
  connection: async () => undefined,
}));

const mockHeaders = jest.fn();
jest.mock('next/headers', () => ({
  headers: () => mockHeaders(),
}));

const mockFlags = { isSpecificFeedback: false };
jest.mock('@/config/feature-flags', () => ({
  featureFlags: {
    get isSpecificFeedback() {
      return mockFlags.isSpecificFeedback;
    },
  },
}));

const mockFetch = jest.fn();

const dataset = {
  id: 42,
  name: 'A very long timetable data set name',
  description: 'desc',
  organisationId: 7,
  organisationName: 'Org',
  status: 'live',
  revisionId: 9,
  transxchangeVersion: '2.4',
  uploadFileExtension: 'xml',
  lastUpdated: '2 Jan 2026 10:00',
  publishedBy: null,
  error: false,
  dataQuality: null,
  isSubscribed: false,
  feedApi: null,
  serviceNumbers: [],
};

function params(id: string) {
  return { params: Promise.resolve({ id }) };
}

describe('app/data/timetable/dataset/[id] (/timetable/dataset/<pk>/)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFlags.isSpecificFeedback = false;
    mockHeaders.mockResolvedValue(new Headers());
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  it.each(['foo', 'downloads', '12abc', 'a-1'])(
    'calls notFound() without fetching for non-numeric id "%s"',
    async (id) => {
      await expect(DatasetDetailPage(params(id))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
      expect(mockFetch).not.toHaveBeenCalled();
    },
  );

  it('fetches the public data-host browser endpoint, forwarding the visitor cookie', async () => {
    mockHeaders.mockResolvedValue(new Headers({ cookie: 'sessionid=abc' }));
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await DatasetDetailPage(params('42'));

    const [url, init] = mockFetch.mock.calls[0];
    expect(String(url)).toContain('/api/browser/timetables/42/');
    expect(String(url)).not.toContain('/api/v1/');
    const sent = init.headers as Headers;
    expect(sent.get('cookie')).toBe('sessionid=abc');
    expect(sent.get('host')).toBeTruthy();
    expect(sent.get('x-forwarded-host')).toBe(sent.get('host'));
  });

  it('renders for an anonymous visitor (no cookie is required)', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await expect(DatasetDetailPage(params('42'))).resolves.toBeTruthy();
    expect((mockFetch.mock.calls[0][1].headers as Headers).has('cookie')).toBe(false);
  });

  it('builds Django-matching breadcrumbs with the name truncated like truncatechars:19', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    const page = await DatasetDetailPage(params('42'));
    const items = page.props.breadcrumbs as Array<{ label: string; href?: string; current?: boolean }>;

    expect(items.map((item) => item.label)).toEqual([
      'Bus Open Data Service',
      'Find Bus Open Data',
      'Browse',
      'Timetables Data',
      'A very long timeta…',
    ]);
    expect(items[2].href).toBe(dataPath('/search'));
    expect(items[3].href).toBe(dataPath('/timetable?status=live'));
    expect(items[4].href).toBe(dataPath('/timetable/dataset/42'));
    expect(items[4].current).toBeFalsy();
  });

  it('passes the is_specific_feedback flag through to the content', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));
    mockFlags.isSpecificFeedback = true;

    const page = await DatasetDetailPage(params('42'));

    expect(page.props.children.props.isSpecificFeedback).toBe(true);
  });

  it('calls notFound() when Django 404s (unknown, hidden or wrong-type id)', async () => {
    mockFetch.mockResolvedValue(new Response('{"error":"Dataset not found"}', { status: 404 }));

    await expect(DatasetDetailPage(params('999999'))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('throws (a 500, like Django) instead of a 404 when Django fails', async () => {
    mockFetch.mockResolvedValue(new Response('boom', { status: 500 }));

    await expect(DatasetDetailPage(params('60'))).rejects.toThrow('Failed to fetch timetables dataset 60: 500');
  });

  it('uses Django’s "Data set details" title for an existing dataset', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    expect(await generateMetadata(params('42'))).toEqual({ title: 'Data set details' });
  });

  it('uses the 404 page title when the dataset is missing', async () => {
    mockFetch.mockResolvedValue(new Response('{}', { status: 404 }));

    expect(await generateMetadata(params('42'))).toEqual({ title: 'Page not found - Bus Open Data Service' });
  });

  it('uses the 404 page title and skips the fetch for non-numeric ids', async () => {
    expect(await generateMetadata(params('foo'))).toEqual({ title: 'Page not found - Bus Open Data Service' });
    expect(mockFetch).not.toHaveBeenCalled();
  });
});
