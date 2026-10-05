import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ObservationListPage from './page';
import { api } from '@/lib/api-client';

let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '12', datasetId: '34', reportId: '56', slug: 'stop-not-in-naptan' }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => '/publish/org/12/dataset/timetable/34/report/56/stop-not-in-naptan',
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn(), post: jest.fn() },
}));

const mockGet = api.get as jest.Mock;
const mockPost = api.post as jest.Mock;
const apiPath = '/api/publish/timetables/data-quality-report/12/34/56/observations/stop-not-in-naptan/';

const response = {
  reportId: 56,
  revisionId: 78,
  isPublished: false,
  observation: {
    title: 'Stop not found in NaPTAN',
    level: 'Advisory',
    text: 'Definition with <a href="https://naptan.example">NaPTAN</a>',
    impacts: 'Impact text',
    resolve: 'Resolve text',
    preamble: 'The following service(s) have stops not in NaPTAN.',
    isActive: true,
    extraInfo: [],
  },
  hasDetail: true,
  canSuppress: true,
  page: 1,
  totalPages: 1,
  totalCount: 2,
  rows: [
    { serviceCode: 'PB1:1', lineName: '1', details: 'There is at least one stop', isSuppressed: false },
    { serviceCode: 'PB2:1', lineName: '2', details: 'There is at least one stop', isSuppressed: true },
  ],
};

describe('Data quality observation list page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    mockPost.mockResolvedValue({ updated: 1 });
  });

  it('renders the observation definition and affected services', async () => {
    mockGet.mockResolvedValue(response);

    render(<ObservationListPage />);

    expect(await screen.findByRole('heading', { name: 'Stop not found in NaPTAN', level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith(`${apiPath}?page=1`);
    expect(document.title).toBe('Stop not found in NaPTAN observations list');
    expect(screen.getByRole('link', { name: 'NaPTAN' })).toHaveAttribute('href', 'https://naptan.example');
    expect(screen.getByRole('heading', { name: 'How to resolve' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute(
      'href',
      '/publish/org/12/dataset/timetable/34/report/draft',
    );
    expect(screen.getByRole('columnheader', { name: 'Service (2)' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: '1 - PB1:1' })).toHaveAttribute(
      'href',
      '/publish/org/12/dataset/timetable/34/review/detail?line=1&revision_id=78&service=PB1%3A1',
    );
    expect(screen.getAllByRole('link', { name: 'There is at least one stop' })[0]).toHaveAttribute(
      'href',
      '/publish/org/12/dataset/timetable/34/report/56/stop-not-in-naptan/detail?line=1&service=PB1%3A1',
    );
    expect(screen.getByRole('checkbox', { name: 'Suppress' })).not.toBeChecked();
    expect(screen.getByRole('checkbox', { name: 'Suppressed' })).toBeChecked();
  });

  it('suppresses a single service', async () => {
    mockGet.mockResolvedValue(response);
    render(<ObservationListPage />);

    await userEvent.click(await screen.findByRole('checkbox', { name: 'Suppress' }));

    expect(mockPost).toHaveBeenCalledWith(`${apiPath}suppress/`, {
      serviceCode: 'PB1:1',
      lineName: '1',
      isSuppressed: true,
    });
    await waitFor(() => expect(screen.getAllByRole('checkbox', { name: 'Suppressed' })).toHaveLength(2));
    expect(screen.getByRole('button', { name: 'Restore all observations' })).toBeInTheDocument();
  });

  it('suppresses all observations', async () => {
    mockGet.mockResolvedValue(response);
    render(<ObservationListPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Suppress all observations' }));

    expect(mockPost).toHaveBeenCalledWith(`${apiPath}suppress/`, { isSuppressed: true });
    await waitFor(() => expect(screen.getAllByRole('checkbox', { name: 'Suppressed' })).toHaveLength(2));
  });

  it('hides suppression and detail links for critical list-only observations', async () => {
    mockGet.mockResolvedValue({
      ...response,
      isPublished: true,
      hasDetail: false,
      canSuppress: false,
      observation: { ...response.observation, title: 'Incorrect NOC', level: 'Critical' },
      rows: [{ serviceCode: 'PB1:1', lineName: '1', details: 'ABCD is specified', isSuppressed: false }],
    });

    render(<ObservationListPage />);

    const row = await screen.findByRole('row', { name: /ABCD is specified/ });
    expect(within(row).queryByRole('checkbox')).not.toBeInTheDocument();
    expect(within(row).queryByRole('link', { name: 'ABCD is specified' })).not.toBeInTheDocument();
    expect(within(row).getByRole('link', { name: '1 - PB1:1' })).toHaveAttribute(
      'href',
      expect.stringContaining('/timetable/dataset/34/detail/?line=1&service=PB1%3A1'),
    );
    expect(screen.queryByRole('button', { name: /all observations/ })).not.toBeInTheDocument();
  });

  it('shows an error when suppression fails', async () => {
    mockGet.mockResolvedValue(response);
    mockPost.mockRejectedValue(new Error('failed'));
    render(<ObservationListPage />);

    await userEvent.click(await screen.findByRole('checkbox', { name: 'Suppress' }));

    expect(await screen.findByText('Unable to update the observation. Please try again.')).toBeInTheDocument();
    expect(screen.getByRole('checkbox', { name: 'Suppress' })).not.toBeChecked();
  });
});
