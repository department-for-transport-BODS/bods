import { render, screen } from '@testing-library/react';
import { DatasetBrowserPage } from './DatasetBrowserPage';
import { api } from '@/lib/api-client';
import { dataPath } from '@/config/client';

const searchParams = new URLSearchParams('status=live');
const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  usePathname: () => '/fares',
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => searchParams,
}));

jest.mock('@/lib/api-client', () => ({ api: { get: jest.fn() } }));
jest.mock('@/hooks/useFilterOptions', () => ({
  useFilterOptions: () => ({ areas: [], organisations: [] }),
}));

const props = {
  title: 'Fares data',
  breadcrumbLabel: 'Fares Data',
  description: 'Search for a specific operator or NOC',
  placeholder: 'Search by NOC or Operator',
  endpointPath: '/api/browser/fares/',
  typeLabel: 'Fares data',
  idLabel: 'Data set ID:',
  lastUpdatedLabel: 'Last updated:',
};

function mockDataset(bodsCompliance?: boolean | null) {
  jest.mocked(api.get).mockResolvedValue({
    results: [{
      id: 83504,
      name: 'Arriva UK Bus',
      operatorName: 'Arriva UK Bus',
      status: 'live',
      modified: '2026-10-12T11:04:39Z',
      bodsCompliance,
    }],
  });
}

describe('dataset browser compliance', () => {
  afterEach(() => jest.clearAllMocks());

  it('links the timetable Browse breadcrumb to search', async () => {
    mockDataset();
    render(
      <DatasetBrowserPage
        {...props}
        title="Timetable data"
        breadcrumbLabel="Timetable Data"
        endpointPath="/api/browser/timetables/"
        typeLabel="Timetable data"
      />,
    );

    await screen.findByText('83504');
    expect(screen.getByRole('link', { name: 'Browse', exact: true })).toHaveAttribute(
      'href', dataPath('/search'),
    );
  });

  it.each([
    [true, 'Compliant'],
    [false, 'Non compliant'],
  ])('renders compliance %s as %s', async (bodsCompliance, label) => {
    mockDataset(bodsCompliance);
    render(<DatasetBrowserPage {...props} includeComplianceInResult />);

    expect(await screen.findByText('BODS compliant data:')).toBeInTheDocument();
    expect(screen.getByText(label)).toBeInTheDocument();
    expect(api.get).toHaveBeenCalledWith('/api/data/browser/fares/?limit=500');
  });

  it('does not add compliance to other dataset browsers', async () => {
    mockDataset(true);
    render(<DatasetBrowserPage {...props} />);

    await screen.findByText('83504');
    expect(screen.queryByText('BODS compliant data:')).not.toBeInTheDocument();
  });

  it.each([null, undefined])('does not invent compliance for %s', async (bodsCompliance) => {
    mockDataset(bodsCompliance);
    render(<DatasetBrowserPage {...props} includeComplianceInResult />);

    await screen.findByText('83504');
    expect(screen.queryByText('BODS compliant data:')).not.toBeInTheDocument();
  });
});
