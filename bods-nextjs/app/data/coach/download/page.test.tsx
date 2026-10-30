import { render, screen } from '@testing-library/react';
import { api } from '@/lib/api-client';
import CoachDownloadPage from './page';

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

describe('Coach download page', () => {
  beforeEach(() => jest.clearAllMocks());

  it('is public and links the TxC and ATCO files from the API', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      txcFile: 'https://example.test/txc.zip',
      atcoFile: 'https://example.test/atco.zip',
    });

    render(<CoachDownloadPage />);

    expect(api.get).toHaveBeenCalledWith('/api/data/browser/downloads/coach/');
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('All coach data');
    expect(
      await screen.findByRole('link', { name: 'All - Download coach data in TransXchange2.4 PTI' }),
    ).toHaveAttribute('href', 'https://example.test/txc.zip');
    expect(screen.getByRole('link', { name: 'All - Download coach data in ATCO-CIF' })).toHaveAttribute(
      'href',
      'https://example.test/atco.zip',
    );
    expect(screen.getByRole('link', { name: 'All Coach Data' })).toHaveAttribute(
      'href',
      expect.stringContaining('/coach/download'),
    );
  });
});
