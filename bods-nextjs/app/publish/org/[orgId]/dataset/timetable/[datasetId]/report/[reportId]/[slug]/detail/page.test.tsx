import { act, render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ObservationDetailPage from './page';
import { api } from '@/lib/api-client';

let mockSlug = 'duplicate-journey-code';
let mockQuery = 'line=42&service=PB1%3A1';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '12', datasetId: '34', reportId: '56', slug: mockSlug }),
  useSearchParams: () => new URLSearchParams(mockQuery),
  usePathname: () => '/publish/org/12/dataset/timetable/34/report/56/slug/detail',
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;

const baseResponse = {
  reportId: 56,
  title: 'Duplicate journey code',
  subtitle: 'Service 42 has at least one journey with a duplicate journey code',
  subtitleDescription: 'Which journeys have been affected?',
  totalDescription: 'Total vehicle journeys',
  totalDescriptionShort: 'affected',
  listText: 'vehicle journeys for this service',
  isFeedback: false,
  canSuppress: false,
  columns: [
    { key: 'journey_start_time', label: 'Journey start time' },
    { key: 'journey_code', label: 'Journey code' },
  ],
  page: 1,
  totalPages: 1,
  totalCount: 1,
  rows: [{ rowId: 0, isSuppressed: false, feedback: '', values: { journey_start_time: '08:15', journey_code: 'JC1' } }],
};

describe('Data quality observation detail page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSlug = 'duplicate-journey-code';
    mockQuery = 'line=42&service=PB1%3A1';
  });

  it('removes stale feedback actions while another service loads and after failure', async () => {
    mockSlug = 'feedback';
    mockGet.mockResolvedValueOnce({
      ...baseResponse,
      isFeedback: true,
      canSuppress: true,
      columns: [{ key: 'message', label: 'Message' }],
      rows: [{ rowId: 9, isSuppressed: false, feedback: '', values: { message: 'Service 42 feedback' } }],
    });
    let rejectRequest: (reason: Error) => void = () => {
      throw new Error('The next service request has not started');
    };
    mockGet.mockImplementationOnce(() => new Promise((_, reject) => { rejectRequest = reject; }));
    const { rerender } = render(<ObservationDetailPage />);
    await screen.findByText('Service 42 feedback');

    mockQuery = 'line=43&service=PB2%3A1';
    rerender(<ObservationDetailPage />);

    expect(screen.queryByText('Service 42 feedback')).not.toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await act(async () => rejectRequest(new Error('Request failed')));
    expect(await screen.findByText('Unable to load the observation details. Please refresh and try again.')).toBeInTheDocument();
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
    expect(mockPost).not.toHaveBeenCalled();
  });

  it('renders affected journeys for the service', async () => {
    mockGet.mockResolvedValue(baseResponse);

    render(<ObservationDetailPage />);

    expect(
      await screen.findByRole('heading', {
        name: 'Service 42 has at least one journey with a duplicate journey code',
        level: 1,
      }),
    ).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(
      '/api/publish/timetables/data-quality-report/12/34/56/observations/duplicate-journey-code/detail/?line=42&service=PB1%3A1&page=1',
    );
    expect(document.title).toBe('Duplicate journey code observation detail');
    expect(screen.getByText(/that are affected by the “Duplicate journey code” data quality observation/)).toBeInTheDocument();
    expect(screen.getByRole('row', { name: '08:15 JC1' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute(
      'href',
      '/publish/org/12/dataset/timetable/34/report/56/duplicate-journey-code',
    );
    expect(screen.queryByRole('checkbox')).not.toBeInTheDocument();
  });

  it('shows feedback messages and suppresses individual feedback', async () => {
    mockSlug = 'feedback';
    mockPost.mockResolvedValue({ updated: 1 });
    mockGet.mockResolvedValue({
      ...baseResponse,
      title: 'Consumer feedback',
      isFeedback: true,
      canSuppress: true,
      columns: [{ key: 'message', label: 'Message' }],
      rows: [
        { rowId: 9, isSuppressed: false, feedback: 'Bus was late', values: { message: 'Read message here' } },
        { rowId: 10, isSuppressed: false, feedback: 'Wrong stop', values: { message: 'Read message here' } },
      ],
    });

    render(<ObservationDetailPage />);

    await userEvent.click((await screen.findAllByText('Read message here'))[0]);
    expect(screen.getByText('Bus was late')).toBeVisible();

    await userEvent.click(screen.getAllByRole('checkbox', { name: 'Suppress' })[0]);

    expect(mockPost).toHaveBeenCalledWith(
      '/api/publish/timetables/data-quality-report/12/34/56/observations/feedback/suppress/',
      { serviceCode: 'PB1:1', lineName: '42', rowId: 9, isSuppressed: true },
    );
    await waitFor(() => expect(screen.getByRole('checkbox', { name: 'Suppressed' })).toBeChecked());
    expect(screen.getByRole('checkbox', { name: 'Suppress' })).not.toBeChecked();
  });

  it('opens one feedback message popup at a time and closes it', async () => {
    mockSlug = 'feedback';
    mockGet.mockResolvedValue({
      ...baseResponse,
      isFeedback: true,
      columns: [{ key: 'message', label: 'Message' }],
      rows: [
        { rowId: 9, isSuppressed: false, feedback: 'Bus was late', values: { message: 'Read message here' } },
        { rowId: 10, isSuppressed: false, feedback: 'Wrong stop', values: { message: 'Read message here' } },
      ],
    });

    render(<ObservationDetailPage />);

    const [first, second] = await screen.findAllByTitle('More information');
    expect(first).toHaveAttribute('aria-expanded', 'false');

    await userEvent.click(first);
    expect(first).toHaveAttribute('aria-expanded', 'true');
    expect(document.getElementById('feedback-1')).toHaveClass('showtooltip');

    await userEvent.click(second);
    expect(first).toHaveAttribute('aria-expanded', 'false');
    expect(second).toHaveAttribute('aria-expanded', 'true');
    expect(document.getElementById('feedback-1')).not.toHaveClass('showtooltip');

    await userEvent.click(screen.getAllByRole('button', { name: 'Close' })[1]);
    expect(second).toHaveAttribute('aria-expanded', 'false');
    expect(document.getElementById('feedback-2')).not.toHaveClass('showtooltip');
  });
});
