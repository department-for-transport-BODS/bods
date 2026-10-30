import { render, screen } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { dataPath } from '@/config/client';
import DisruptionsDownloadPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

describe('Disruptions download page', () => {
  beforeEach(() => jest.clearAllMocks());

  it('offers SIRI-SX and GTFS-RT downloads when service alerts are live', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      showBulkArchiveUrl: true,
      isGtfsServiceAlertsLive: true,
    });

    render(<DisruptionsDownloadPage />);

    expect(api.get).toHaveBeenCalledWith('/api/data/browser/downloads/disruptions/');
    expect(
      await screen.findByRole('link', { name: 'Download all disruption data in SIRI-SX format' }),
    ).toHaveAttribute('href', dataPath('/disruptions/download/bulk_archive'));
    expect(
      screen.getByRole('link', { name: 'Download all disruption data in GTFS-RT format' }),
    ).toHaveAttribute('href', dataPath('/disruptions/download/gtfsrt_service_alerts'));
    expect(screen.getByLabelText('Heading Title')).toHaveTextContent('All disruption data');
    expect(screen.getByRole('button', { name: 'Help: GTFS-RT' })).toBeInTheDocument();
  });

  it('hides GTFS-RT when the service alerts flag is off', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      showBulkArchiveUrl: true,
      isGtfsServiceAlertsLive: false,
    });

    render(<DisruptionsDownloadPage />);

    await screen.findByRole('link', { name: 'Download all disruption data in SIRI-SX format' });
    expect(screen.queryByText(/GTFS-RT/)).not.toBeInTheDocument();
  });

  it('shows the unavailable message when no archive exists', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      showBulkArchiveUrl: false,
      isGtfsServiceAlertsLive: true,
    });

    render(<DisruptionsDownloadPage />);

    expect(
      await screen.findByText('Bulk download is not yet available. Please check back later.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: /Download all disruption data/ })).not.toBeInTheDocument();
  });
});
