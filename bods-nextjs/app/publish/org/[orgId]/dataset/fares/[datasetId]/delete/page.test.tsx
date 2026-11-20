import { render, screen, waitFor } from '@testing-library/react';
import { publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';
import FaresDeletePage from './page';

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

const statusUrl = '/api/publish/fares/review-status/7/42/';
const datasetUrl = publishAppPath('/org/7/dataset/fares/42');

function mockApi({ hasLiveRevision, liveStatus }: { hasLiveRevision: boolean; liveStatus?: string }) {
  (api.get as jest.Mock).mockImplementation(async (url: string) => {
    if (url === `${statusUrl}?revision=live`) {
      return { status: liveStatus };
    }
    return { name: 'Fares data set', hasLiveRevision, status: 'success' };
  });
}

describe('FaresDeletePage back and cancel links', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('goes back and cancels to the review page when there is no live revision', async () => {
    mockApi({ hasLiveRevision: false });
    render(<FaresDeletePage />);

    expect(await screen.findByText(/delete data set "Fares data set"/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', `${datasetUrl}/review`);
    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', `${datasetUrl}/review`);
    expect(api.get).toHaveBeenCalledTimes(1);
  });

  it('goes back to the dataset detail and cancels to the update review page for a live, non-expired revision', async () => {
    mockApi({ hasLiveRevision: true, liveStatus: 'live' });
    render(<FaresDeletePage />);

    expect(await screen.findByText(/cancel updating data set "Fares data set"/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', datasetUrl);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith(`${statusUrl}?revision=live`));
    await waitFor(() =>
      expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', `${datasetUrl}/update/review`),
    );
  });

  it('goes back and cancels to the dataset detail when the live revision is expired', async () => {
    mockApi({ hasLiveRevision: true, liveStatus: 'expired' });
    render(<FaresDeletePage />);

    expect(await screen.findByText(/cancel updating data set "Fares data set"/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', datasetUrl);
    await waitFor(() => expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', datasetUrl));
  });
});
