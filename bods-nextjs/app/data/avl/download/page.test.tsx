import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api } from '@/lib/api-client';
import { dataPath } from '@/config/client';
import AvlDownloadPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

describe('AVL download page', () => {
  beforeEach(() => jest.clearAllMocks());

  it('links the three bulk archives when one exists', async () => {
    (api.get as jest.Mock).mockResolvedValue({ showBulkArchiveUrl: true });

    render(<AvlDownloadPage />);

    expect(api.get).toHaveBeenCalledWith('/api/data/browser/downloads/avl/');
    expect(await screen.findByRole('heading', { level: 3, name: 'Download file' })).toBeInTheDocument();
    expect(screen.getByLabelText('Heading Title')).toHaveTextContent('All location data');
    expect(
      screen.getByRole('link', { name: 'Download all bus location data in SIRI-VM format' }),
    ).toHaveAttribute('href', dataPath('/avl/download/bulk_archive'));
    expect(
      screen.getByRole('link', { name: 'Download all bus location data in GTFS RT format' }),
    ).toHaveAttribute('href', dataPath('/avl/download/gtfsrt'));
    expect(
      screen.getByRole('link', {
        name: 'Download all bus location data from Transport for London (TfL) only in SIRI-VM format',
      }),
    ).toHaveAttribute('href', dataPath('/avl/download/sirivm_tfl'));
  });

  it('shows the unavailable message three times when no archive exists', async () => {
    (api.get as jest.Mock).mockResolvedValue({ showBulkArchiveUrl: false });

    render(<AvlDownloadPage />);

    expect(
      await screen.findAllByText('Bulk download is not yet available. Please check back later.'),
    ).toHaveLength(3);
    expect(screen.queryByRole('link', { name: /Download all bus location data/ })).not.toBeInTheDocument();
  });

  it('opens the SIRI-VM help modal from its icon', async () => {
    (api.get as jest.Mock).mockResolvedValue({ showBulkArchiveUrl: true });

    render(<AvlDownloadPage />);

    await userEvent.click(await screen.findByRole('button', { name: 'Help: SIRI-VM' }));

    const overlays = screen.getAllByTestId('help-overlay');
    expect(overlays.some((overlay) => overlay.classList.contains('active'))).toBe(true);
  });
});
