import { render, screen } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { dataPath } from '@/config/client';
import FaresDownloadPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

describe('Fares download page', () => {
  beforeEach(() => jest.clearAllMocks());

  it('links the bulk archive and lists the file attributes', async () => {
    (api.get as jest.Mock).mockResolvedValue({ showBulkArchiveUrl: true });

    render(<FaresDownloadPage />);

    expect(api.get).toHaveBeenCalledWith('/api/data/browser/downloads/fares/');
    expect(await screen.findByRole('link', { name: 'Download all fares data' })).toHaveAttribute(
      'href',
      dataPath('/fares/download/bulk_archive'),
    );
    expect(screen.getByLabelText('Heading Title')).toHaveTextContent('All fares data');
    expect(screen.getByText('Daily around 6:00 am GMT', { exact: false })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Help: NeTEx' })).toBeInTheDocument();
  });

  it('shows the unavailable message when no archive exists', async () => {
    (api.get as jest.Mock).mockResolvedValue({ showBulkArchiveUrl: false });

    render(<FaresDownloadPage />);

    expect(
      await screen.findByText('Bulk download is not yet available. Please check back later.'),
    ).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Download all fares data' })).not.toBeInTheDocument();
  });
});
