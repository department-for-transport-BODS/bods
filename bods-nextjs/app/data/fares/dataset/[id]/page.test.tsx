/** @jest-environment node */

import { dataPath } from '@/config/client';
import FaresDatasetDetailPage, { generateMetadata } from './page';

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

const mockFlags = { isFaresValidatorActive: false };
jest.mock('@/config/feature-flags', () => ({
  featureFlags: {
    get isFaresValidatorActive() {
      return mockFlags.isFaresValidatorActive;
    },
  },
}));

const mockFetch = jest.fn();

const dataset = {
  id: 42,
  name: 'A very long fares data set name',
  description: 'desc',
  organisationId: 7,
  organisationName: 'Org',
  status: 'live',
  revisionId: 9,
  transxchangeVersion: '',
  uploadFileExtension: 'zip',
  lastUpdated: '2 Jan 2026 10:00',
  publishedBy: null,
  showMap: true,
  isCompliantError: false,
  showReportLink: false,
  metadata: {
    schemaVersion: '1.1',
    numOfFareZones: '1',
    numOfLines: '2',
    numOfSalesOfferPackages: '3',
    numOfFareProducts: '4',
    numOfUserProfiles: '5',
    validFrom: '1 Jan 2026',
    validTo: '2 Jan 2027',
  },
  isSubscribed: false,
  feedApi: null,
};

function params(id: string) {
  return { params: Promise.resolve({ id }) };
}

describe('app/data/fares/dataset/[id] (/fares/dataset/<pk>/)', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockFlags.isFaresValidatorActive = false;
    mockHeaders.mockResolvedValue(new Headers());
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  it.each(['foo', 'downloads', '12abc'])(
    'calls notFound() without fetching for non-numeric id "%s"',
    async (id) => {
      await expect(FaresDatasetDetailPage(params(id))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
      expect(mockFetch).not.toHaveBeenCalled();
    },
  );

  it('fetches the public fares browser endpoint on the data host, forwarding the cookie', async () => {
    mockHeaders.mockResolvedValue(new Headers({ cookie: 'sessionid=abc' }));
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await FaresDatasetDetailPage(params('42'));

    const [url, init] = mockFetch.mock.calls[0];
    expect(String(url)).toContain('/api/browser/fares/42/');
    const sent = init.headers as Headers;
    expect(sent.get('cookie')).toBe('sessionid=abc');
    expect(sent.get('x-forwarded-host')).toBe(sent.get('host'));
  });

  it('renders for an anonymous visitor', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    await expect(FaresDatasetDetailPage(params('42'))).resolves.toBeTruthy();
    expect((mockFetch.mock.calls[0][1].headers as Headers).has('cookie')).toBe(false);
  });

  it('builds Django-matching breadcrumbs and pads the heading', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    const page = await FaresDatasetDetailPage(params('42'));
    const items = page.props.breadcrumbs as Array<{
      label: string;
      href?: string;
    }>;

    expect(page.props.paddedHeading).toBe(true);
    expect(items.map((item) => item.label)).toEqual([
      'Bus Open Data Service',
      'Find Bus Open Data',
      'Browse',
      'Fares Data',
      'A very long fares …',
    ]);
    expect(items[2].href).toBe(dataPath('/search'));
    expect(items[3].href).toBe(dataPath('/fares?status=live'));
    expect(items[4].href).toBe(dataPath('/fares/dataset/42'));
  });

  it.each([true, false])(
    'passes the is_fares_validator_active flag (%s) through to the content',
    async (flag) => {
      mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));
      mockFlags.isFaresValidatorActive = flag;

      const page = await FaresDatasetDetailPage(params('42'));

      expect(page.props.children.props.isFaresValidatorActive).toBe(flag);
    },
  );

  it('calls notFound() when Django 404s (unknown, unpublished or wrong-type id)', async () => {
    mockFetch.mockResolvedValue(new Response('{"error":"Dataset not found"}', { status: 404 }));

    await expect(FaresDatasetDetailPage(params('999999'))).rejects.toThrow('NEXT_HTTP_ERROR_FALLBACK;404');
  });

  it('throws (a 500, like Django) instead of a 404 when Django fails', async () => {
    mockFetch.mockResolvedValue(new Response('boom', { status: 500 }));

    await expect(FaresDatasetDetailPage(params('60'))).rejects.toThrow(
      'Failed to fetch fares dataset 60: 500',
    );
  });

  it('uses Django’s "Data set details" title, without a suffix', async () => {
    mockFetch.mockResolvedValue(new Response(JSON.stringify(dataset), { status: 200 }));

    expect(await generateMetadata(params('42'))).toEqual({
      title: { absolute: 'Data set details' },
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
