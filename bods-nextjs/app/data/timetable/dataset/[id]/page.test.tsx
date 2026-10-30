/** @jest-environment node */

import { dataPath } from '@/config/client';
import DatasetDetailPage, { generateMetadata } from './page';

jest.mock('next/navigation', () => ({
  notFound: () => {
    throw new Error('NEXT_HTTP_ERROR_FALLBACK;404');
  },
}));

jest.mock('next/headers', () => ({
  headers: async () => new Headers(),
}));

const mockFetch = jest.fn();

describe('app/data/timetable/dataset/[id] (/timetable/dataset/<pk>/)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  it.each(['foo', 'downloads', '12abc', 'a-1'])(
    'calls notFound() without fetching for non-numeric id "%s"',
    async (id) => {
      await expect(DatasetDetailPage({ params: Promise.resolve({ id }) })).rejects.toThrow(
        'NEXT_HTTP_ERROR_FALLBACK;404',
      );
      expect(mockFetch).not.toHaveBeenCalled();
    },
  );

  it('calls notFound() for a wrong-type id (e.g. an AVL id), which the timetable-only dataset API 404s', async () => {
    mockFetch.mockResolvedValue(new Response('{"detail":"Not found."}', { status: 404 }));

    await expect(DatasetDetailPage({ params: Promise.resolve({ id: '7' }) })).rejects.toThrow(
      'NEXT_HTTP_ERROR_FALLBACK;404',
    );
  });

  it('renders the dataset with Django-matching breadcrumb links', async () => {
    mockFetch.mockResolvedValue(
      new Response(
        JSON.stringify({
          id: 42,
          organisationId: 1,
          revisionId: 9,
          modified: '2026-01-02T10:00:00Z',
          name: 'My timetable',
          description: '',
          status: 'live',
          url: 'http://data.example/timetable/dataset/42/download/',
          extension: 'xml',
          lines: [],
          adminAreas: [],
          dqRag: 'unavailable',
        }),
        { status: 200 },
      ),
    );

    const page = await DatasetDetailPage({ params: Promise.resolve({ id: '42' }) });
    const breadcrumbs = page.props.children[0].props.items as Array<{ label: string; href?: string }>;

    expect(breadcrumbs.find((item) => item.label === 'Timetables Data')?.href).toBe(
      dataPath('/timetable?status=live'),
    );
  });

  it('calls notFound() when a numeric id does not exist in Django', async () => {
    mockFetch.mockResolvedValue(new Response('{}', { status: 404 }));

    await expect(
      DatasetDetailPage({ params: Promise.resolve({ id: '999999' }) }),
    ).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
    expect(mockFetch).toHaveBeenCalledTimes(1);
  });

  it('still looks up numeric ids via the Django dataset API', async () => {
    mockFetch.mockResolvedValue(new Response('{}', { status: 404 }));

    await DatasetDetailPage({ params: Promise.resolve({ id: '42' }) }).catch(() => undefined);

    expect(String(mockFetch.mock.calls[0][0])).toContain('/api/v1/dataset/42/');
  });

  it('uses the 404 page title and skips the fetch for non-numeric ids', async () => {
    const metadata = await generateMetadata({ params: Promise.resolve({ id: 'foo' }) });

    expect(metadata).toEqual({ title: 'Page not found - Bus Open Data Service' });
    expect(mockFetch).not.toHaveBeenCalled();
  });
});
