import { render, screen, waitFor } from '@testing-library/react';
import { ApiError, api } from '@/lib/api-client';
import LineDetailPageContent from './LineDetailPageContent';

const mockNotFound = jest.fn();
let mockSearchParams = new URLSearchParams('line=14&service=PB2044957%3A14');

jest.mock('next/navigation', () => ({
  useParams: () => ({ id: '1' }),
  useSearchParams: () => mockSearchParams,
  useRouter: () => ({ push: jest.fn() }),
  notFound: () => mockNotFound(),
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

const stop = {
  name: 'High Street',
  atcoCode: '0100BRP90310',
  street: 'High St',
  indicator: 'Stop A',
  stopType: 'BCT',
  observation: null,
};

const line = {
  datasetId: 1,
  datasetName: 'Local Import Org_upload',
  revisionId: 1,
  lineName: '14',
  serviceCode: 'PB2044957:14',
  serviceType: 'Standard',
  currentValidFiles: [],
  bookingArrangements: null,
  bookingMethods: null,
  timetable: {
    currDate: '2024-05-01',
    isTimetableInfoAvailable: true,
    directions: [
      {
        direction: 'outbound',
        journeyName: 'Outbound - A to B',
        isEmpty: false,
        totalPage: 1,
        currPage: 1,
        showAll: false,
        totalRowCount: 1,
        pageParam: 'outbound_page',
        showAllParam: 'showAllOutbound',
        columns: [
          { name: 'Journey Code', observation: null },
          { name: 'JC1', observation: null },
        ],
        rows: [{ index: 0, stop, cells: [{ departureTime: '07:00', journeyId: 5, observations: [] }] }],
      },
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

function renderPage({ isTimetableVisualiserActive = true, isSpecificFeedback = true } = {}) {
  return render(
    <LineDetailPageContent
      isTimetableVisualiserActive={isTimetableVisualiserActive}
      isSpecificFeedback={isSpecificFeedback}
    />,
  );
}

describe('Data line detail page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams('line=14&service=PB2044957%3A14');
  });

  it('renders the line, its properties and the map timestamp placeholder', async () => {
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByRole('heading', { name: '14', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(
      '/api/data/browser/timetables/1/line-detail/?line=14&service=PB2044957%3A14&includeTimetable=true',
    );
    expect(document.title).toBe('14');
    expect(screen.getByText('Overview of the available bus open data')).toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'Type of service' })).toHaveClass('govuk-!-width-one-half');
    expect(screen.getByRole('cell', { name: 'N/A' })).toBeInTheDocument();
    expect(document.getElementById('map-updated-timestamp')).toHaveTextContent('-');
    expect(screen.getByRole('link', { name: 'Local Import Org_u…' })).toBeInTheDocument();
  });

  it('skips empty directions and shows Add Feedback links when specific feedback is on', async () => {
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByText('Outbound - A to B')).toBeInTheDocument();
    expect(screen.queryByText('Inbound - B to A')).not.toBeInTheDocument();
    expect(screen.getAllByRole('link', { name: 'Add Feedback' }).length).toBeGreaterThan(0);
  });

  it('asks for service feedback when a service is selected and specific feedback is on', async () => {
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByRole('heading', { name: 'Noticed issues with this service?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Provide feedback about this service' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/feedback\/\?line=14&service=PB2044957%3A14$/),
    );
  });

  it('falls back to data set feedback when specific feedback is off', async () => {
    mockGet.mockResolvedValue(line);
    renderPage({ isSpecificFeedback: false });

    expect(await screen.findByRole('heading', { name: 'Noticed issues with this data set?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact data set owner directly' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/feedback\/$/),
    );
    expect(screen.queryByRole('link', { name: 'Add Feedback' })).not.toBeInTheDocument();
  });

  it('falls back to data set feedback when no service is selected', async () => {
    mockSearchParams = new URLSearchParams('line=14');
    mockGet.mockResolvedValue(line);
    renderPage();

    expect(await screen.findByRole('heading', { name: 'Noticed issues with this data set?' })).toBeInTheDocument();
  });

  it('skips the timetable when the visualiser flag is off', async () => {
    mockGet.mockResolvedValue({ ...line, timetable: null });
    renderPage({ isTimetableVisualiserActive: false });

    expect(await screen.findByRole('heading', { name: '14', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(expect.stringContaining('includeTimetable=false'));
    expect(screen.queryByRole('heading', { name: 'Filter by' })).not.toBeInTheDocument();
  });

  it('calls notFound when the API returns 404', async () => {
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));
    renderPage();

    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });
});
