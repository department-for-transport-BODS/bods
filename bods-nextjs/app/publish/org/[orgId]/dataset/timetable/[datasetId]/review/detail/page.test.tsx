import { render, screen, waitFor } from '@testing-library/react';
import { ApiError, api } from '@/lib/api-client';
import LineDetailPageContent from './LineDetailPageContent';

const mockNotFound = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
  useSearchParams: () => new URLSearchParams('line=line1&revision_id=10&service=PB0000000%3A1'),
  useRouter: () => ({ push: jest.fn() }),
  notFound: () => mockNotFound(),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/components/data/MapboxRouteMap', () => ({
  MapboxRouteMap: ({ ariaLabel }: { ariaLabel: string }) => <div aria-label={ariaLabel} />,
}));

jest.mock('air-datepicker', () => ({ __esModule: true, default: class { destroy() {} } }));
jest.mock('air-datepicker/locale/en', () => ({ __esModule: true, default: {} }));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

const mockGet = api.get as jest.Mock;

const line = {
  orgId: 1,
  datasetId: 9,
  feedName: 'A very long publisher feed name',
  revisionId: 10,
  lineName: 'line1',
  serviceCode: 'PB0000000:1',
  serviceType: 'Flexible',
  currentValidFiles: [
    { filename: 'a.xml', startDate: '01-01-2024', endDate: null },
    { filename: 'b.xml', startDate: null, endDate: '31-12-2024' },
  ],
  bookingArrangements: null,
  bookingMethods: { phone: '0123', email: null, url: null },
  timetable: {
    currDate: '2024-05-01',
    isTimetableInfoAvailable: true,
    directions: [
      {
        direction: 'inbound',
        journeyName: 'Inbound - B to A',
        isEmpty: true,
        totalPage: 0,
        currPage: 1,
        showAll: false,
        totalRowCount: 0,
        pageParam: 'inbound_page',
        showAllParam: 'showAllInbound',
        columns: [{ name: 'Journey Code', observation: null }],
        rows: [],
      },
    ],
  },
};

function renderPage({ isTimetableVisualiserActive = true } = {}) {
  return render(<LineDetailPageContent isTimetableVisualiserActive={isTimetableVisualiserActive} />);
}

describe('Publish line detail page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the line, its properties and the help links', async () => {
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByRole('heading', { name: 'line1', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(
      '/api/publish/timetables/line-detail/1/9/?line=line1&revision_id=10&service=PB0000000%3A1&includeTimetable=true',
    );
    expect(document.title).toBe('line1');
    expect(screen.getByText('Preview your service data status and make changes')).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'Type of service' })).toBeInTheDocument();
    expect(screen.getByText(/01-01-2024 - No End Date/)).toBeInTheDocument();
    expect(screen.getByText(/No Start Date - 31-12-2024/)).toBeInTheDocument();
    expect(screen.getByText('No currently valid files available in this dataset for this service')).toBeInTheDocument();
    expect(screen.getByText(/Phone - 0123/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      expect.stringContaining('/guidance/operator-requirements'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute(
      'href',
      expect.stringContaining('/contact'),
    );
    expect(screen.getByRole('link', { name: 'A very long publish...' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/1/dataset/timetable/9/review'),
    );
  });

  it('renders every direction of the visualiser, without feedback links, when the flag is on', async () => {
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByText('Inbound - B to A')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Add Feedback' })).not.toBeInTheDocument();
  });

  it('skips the timetable when the visualiser flag is off', async () => {
    mockGet.mockResolvedValue({ ...line, timetable: null });
    renderPage({ isTimetableVisualiserActive: false });

    expect(await screen.findByRole('heading', { name: 'line1', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('includeTimetable=false'));
    expect(screen.queryByRole('heading', { name: 'Filter by' })).not.toBeInTheDocument();
  });

  it('calls notFound when the API returns 404', async () => {
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));
    renderPage();

    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error summary for other failures', async () => {
    mockGet.mockRejectedValue(new ApiError('Boom', 500, {}));
    renderPage();

    expect(
      await screen.findByText('Unable to load the service details. Please refresh and try again.'),
    ).toBeInTheDocument();
  });
});
