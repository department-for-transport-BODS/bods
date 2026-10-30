/** @jest-environment node */

import { dataPath } from '@/config/client';
import AvlDatasetDetailPage, { generateMetadata } from './page';

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

const mockFetch = jest.fn();

const dataset = {
  id: 42,
  name: 'A very long location data feed name',
  description: 'desc',
  organisationId: 7,
  organisationName: 'Org',
  status: 'live',
  revisionId: 9,
  lastUpdated: '2 Jan 2026 10:00',
  lastAutomatedUpdate: '3 Jan 2026 11:00',
  siriVmVersion: '2.0',
  avlTimetablesMatching: '85%',
  isSubscribed: false,
  feedApi: null,
};

function params(id: string) {
  return { params: Promise.resolve({ id }) };
}

describe('app/data/avl/dataset/[id] (/avl/dataset/<pk>/)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockHeaders.mockResolvedValue(new Headers());
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  it.each(['foo', 'downloads', '12abc'])(
    'calls notFound() without fetching for non-numeric id "%s"',
    async (id) => {
      await expect(AvlDatasetDetailPage(params(id))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
      expect(mockFetch).not.toHaveBeenCalled();
    },
  );

  it('fetches the public AVL browser endpoint on the data host, forwarding the cookie', async () => {
    mockHeaders.mockResolvedValue(new Headers({ cookie: 'sessionid=abc' }));
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await AvlDatasetDetailPage(params('42'));

    const [url, init] = mockFetch.mock.calls[0];
    expect(String(url)).toContain('/api/browser/avl/42/');
    const sent = init.headers as Headers;
    expect(sent.get('cookie')).toBe('sessionid=abc');
    expect(sent.get('x-forwarded-host')).toBe(sent.get('host'));
  });

  it('renders for an anonymous visitor', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await expect(AvlDatasetDetailPage(params('42'))).resolves.toBeTruthy();
    expect((mockFetch.mock.calls[0][1].headers as Headers).has('cookie')).toBe(false);
  });

  it('builds Django-matching breadcrumbs and pads the heading', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    const page = await AvlDatasetDetailPage(params('42'));
    const items = page.props.breadcrumbs as Array<{
      label: string;
      href?: string;
    }>;

    expect(page.props.paddedHeading).toBe(true);
    expect(items.map((item) => item.label)).toEqual([
      'Bus Open Data Service',
      'Find Bus Open Data',
      'Browse',
      'Location Data',
      'A very long locati…',
    ]);
    expect(items[2].href).toBe(dataPath('/search'));
    expect(items[3].href).toBe(dataPath('/avl?status=live'));
    expect(items[4].href).toBe(dataPath('/avl/dataset/42'));
  });

  it('calls notFound() when Django 404s (unknown, unpublished or wrong-type id)', async () => {
    mockFetch.mockResolvedValue(new Response('{"error":"Dataset not found"}', { status: 404 }));

    await expect(AvlDatasetDetailPage(params('999999'))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
  });

  it('throws (a 500, like Django) instead of a 404 when Django fails', async () => {
    mockFetch.mockResolvedValue(new Response('boom', { status: 500 }));

    await expect(AvlDatasetDetailPage(params('60'))).rejects.toThrow('Failed to fetch avl dataset 60: 500');
  });

  it('uses Django’s "Data feed details" title, without a suffix', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    expect(await generateMetadata(params('42'))).toEqual({
      title: { absolute: 'Data feed details' },
    });
  });

  it('uses the 404 page title when the dataset is missing or the id is not numeric', async () => {
    mockFetch.mockResolvedValue(new Response('{}', { status: 404 }));
    expect(await generateMetadata(params('42'))).toEqual({
      title: 'Page not found - Bus Open Data Service',
    });

    mockFetch.mockClear();
    expect(await generateMetadata(params('foo'))).toEqual({
      title: 'Page not found - Bus Open Data Service',
    });
    expect(mockFetch).not.toHaveBeenCalled();
  });
});
