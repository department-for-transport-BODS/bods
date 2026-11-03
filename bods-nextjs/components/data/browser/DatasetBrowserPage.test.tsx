import { render, screen } from '@testing-library/react';
import { DatasetBrowserPage } from './DatasetBrowserPage';
import { api } from '@/lib/api-client';
import { dataPath } from '@/config/client';

const searchParams = new URLSearchParams();
const mockPush = jest.fn();

function setSearchParams(query = '') {
  for (const key of Array.from(searchParams.keys())) {
    searchParams.delete(key);
  }
  new URLSearchParams(query).forEach((value, key) => searchParams.set(key, value));
}

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
  datasetType: 'FARES' as const,
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
  beforeEach(() => setSearchParams());
  afterEach(() => jest.clearAllMocks());

  it('does not display a published filter when no status filter was requested', async () => {
    mockDataset();
    render(<DatasetBrowserPage {...props} />);

    await screen.findByText('83504');
    expect(screen.queryByText('Having trouble finding what you want?')).not.toBeInTheDocument();
    expect(screen.getByLabelText('Status')).toHaveValue('');
    expect(screen.getByRole('region', { name: 'Search filters' })).toBeEmptyDOMElement();
  });

  it('shows the Django no-results help when nothing matches', async () => {
    jest.mocked(api.get).mockResolvedValue({ results: [] });
    render(<DatasetBrowserPage {...props} />);

    expect(
      await screen.findByRole('heading', { name: 'Having trouble finding what you want?' }),
    ).toBeInTheDocument();
    expect(screen.getByText('Check your spelling and try again')).toBeInTheDocument();
  });

  it('displays the Django choice label for an active status filter', async () => {
    setSearchParams('status=live');
    mockDataset();
    render(<DatasetBrowserPage {...props} />);

    await screen.findByText('83504');
    expect(screen.getByLabelText('Status')).toHaveValue('published');
    expect(screen.getByRole('region', { name: 'Search filters' })).toHaveTextContent('Published');
  });

  it('links the timetable Browse breadcrumb to search', async () => {
    mockDataset();
    render(
      <DatasetBrowserPage
        {...props}
        datasetType="TIMETABLE"
        title="Timetable data"
        breadcrumbLabel="Timetable Data"
        endpointPath="/api/browser/timetables/"
        typeLabel="Timetable data"
      />,
    );

    await screen.findByText('83504');
    expect(screen.getByRole('link', { name: 'Browse' })).toHaveAttribute(
      'href', dataPath('/search'),
    );
  });

  it.each([
    ['TIMETABLE', '/timetable/dataset/83504'],
    ['AVL', '/avl/dataset/83504'],
    ['FARES', '/fares/dataset/83504'],
  ] as const)('links %s results to the Django-matching detail URL', async (datasetType, path) => {
    mockDataset();
    render(<DatasetBrowserPage {...props} datasetType={datasetType} />);

    expect(await screen.findByRole('link', { name: /Arriva UK Bus/ })).toHaveAttribute(
      'href',
      dataPath(path),
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
