/** @jest-environment node */

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

describe('app/data/[id] catch-all', () => {
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
