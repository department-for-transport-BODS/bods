import { render, screen, within } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { AlertsBrowserPage } from './AlertsBrowserPage';

const searchParams = new URLSearchParams();
const mockPush = jest.fn();

function setSearchParams(query = '') {
  for (const key of Array.from(searchParams.keys())) {
    searchParams.delete(key);
  }
  new URLSearchParams(query).forEach((value, key) => searchParams.set(key, value));
}

jest.mock('next/navigation', () => ({
  usePathname: () => '/disruptions',
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => searchParams,
}));

jest.mock('@/lib/api-client', () => ({ api: { get: jest.fn() } }));

const props = {
  title: 'Disruption data',
  breadcrumbLabel: 'Disruption Data',
  description: 'Search for a specific Local Transport Authority',
  placeholder: 'Enter Local Transport Authority name',
  endpointPath: '/api/app/disruption_organisations/',
};

describe('AlertsBrowserPage search summary', () => {
  beforeEach(() => {
    setSearchParams();
    jest.mocked(api.get).mockResolvedValue([
      {
        id: 'london',
        name: 'London',
        stats: { lastUpdated: '2026-10-12T11:04:39.000Z', totalDisruptionsCount: 2 },
      },
      {
        id: 'greater-london',
        name: 'Greater London',
        stats: { lastUpdated: '2026-10-12T11:03:39.000Z', totalDisruptionsCount: 1 },
      },
    ]);
  });

  afterEach(() => jest.clearAllMocks());

  it('shows the containing pill when a search term is active', async () => {
    setSearchParams('q=London');
    render(<AlertsBrowserPage {...props} />);

    await screen.findByText('2 results');
    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(within(summary).getByText('Containing')).toBeInTheDocument();
    expect(within(summary).getByText('London')).toHaveClass('app-data-browser__filter-pill-label');
    expect(within(summary).getByRole('link', { name: 'London' })).toHaveAttribute(
      'href',
      '/disruptions?ordering=-modified',
    );
  });

  it('keeps the empty summary bar when there is no search term', async () => {
    render(<AlertsBrowserPage {...props} />);

    await screen.findByText('2 results');
    const summary = screen.getByRole('region', { name: 'Search filters' });
    expect(summary).toBeEmptyDOMElement();
    expect(document.querySelector('hr.pillbox-break')).toBeInTheDocument();
  });
});
