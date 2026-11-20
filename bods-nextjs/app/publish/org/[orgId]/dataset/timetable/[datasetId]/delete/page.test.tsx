import { render, screen, waitFor } from '@testing-library/react';
import { publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';
import TimetableDeletePage from './page';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '7', datasetId: '42' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

const statusUrl = '/api/publish/timetables/review-status/7/42/';
const datasetUrl = publishAppPath('/org/7/dataset/timetable/42');

function mockApi({ hasLiveRevision, liveStatus }: { hasLiveRevision: boolean; liveStatus?: string }) {
  (api.get as jest.Mock).mockImplementation(async (url: string) => {
    if (url === `${statusUrl}?revision=live`) {
      return { status: liveStatus };
    }
    return { name: 'Timetable data set', hasLiveRevision, status: 'success' };
  });
}

// Django's feed_delete.html uses RevisionDeleteTimetableView.get_cancel_url for the back
// link as well as the Cancel button, so both must always point at the same place.
describe('TimetableDeletePage back and cancel links', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('goes back and cancels to the review page when there is no live revision', async () => {
    mockApi({ hasLiveRevision: false });
    render(<TimetableDeletePage />);

    expect(await screen.findByText(/delete data set "Timetable data set"/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Would you like to delete this data set?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', `${datasetUrl}/review`);
    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', `${datasetUrl}/review`);
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it('goes back and cancels to the update review page for a live, non-expired revision', async () => {
    mockApi({ hasLiveRevision: true, liveStatus: 'live' });
    render(<TimetableDeletePage />);

    expect(await screen.findByText(/cancel updating data set "Timetable data set"/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Would you like to cancel updating this data set' })).toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(`${statusUrl}?revision=live`));
    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', `${datasetUrl}/update/review`);
      expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', `${datasetUrl}/update/review`);
    });
  });

  it('goes back and cancels to the dataset detail, with delete copy, when the live revision is expired', async () => {
    mockApi({ hasLiveRevision: true, liveStatus: 'expired' });
    render(<TimetableDeletePage />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', datasetUrl);
      expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', datasetUrl);
    });
    expect(screen.getByRole('heading', { name: 'Would you like to delete this data set?' })).toBeInTheDocument();
    expect(screen.getByText(/delete data set "Timetable data set"/)).toBeInTheDocument();
  });
});
