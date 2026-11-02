import { act, fireEvent, render, screen } from '@testing-library/react';
import { AvlArchivePageContent } from './AvlArchivePageContent';

const mockApiGet = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '12', datasetId: '34' }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: (path: string) => mockApiGet(path) },
  getCsrfToken: () => 'token',
}));

describe('AvlArchivePageContent', () => {
  const originalFetch = global.fetch;
  const mockFetch = jest.fn();

  beforeEach(() => {
    mockApiGet.mockReset();
    mockFetch.mockReset();
    global.fetch = mockFetch as unknown as typeof fetch;
  });

  afterAll(() => {
    global.fetch = originalFetch;
  });

  it('links Back and Cancel to the feed detail page', () => {
    mockApiGet.mockReturnValue(new Promise(() => {}));
    render(<AvlArchivePageContent />);

    for (const name of ['Back', 'Cancel']) {
      const href = screen.getByRole('link', { name }).getAttribute('href');
      expect(href).toMatch(/\/org\/12\/dataset\/avl\/34\/$/);
      expect(href).not.toMatch(/\/publish\/org/);
    }
  });

  it('waits for the feed name before deactivating so the success page can show it', async () => {
    let resolveName: (detail: { name: string }) => void = () => {};
    mockApiGet.mockReturnValue(new Promise((resolve) => { resolveName = resolve; }));
    mockFetch.mockResolvedValue({ ok: false, json: async () => ({ error: 'Stop here' }) });

    render(<AvlArchivePageContent />);
    fireEvent.click(screen.getByRole('button', { name: 'Confirm' }));
    await act(async () => {});
    expect(mockFetch).not.toHaveBeenCalled();

    await act(async () => resolveName({ name: 'My feed' }));

    expect(await screen.findByText('Stop here')).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(
      '/api/next/avl/archive?orgId=12&datasetId=34',
      expect.objectContaining({ method: 'POST' }),
    );
  });
});
