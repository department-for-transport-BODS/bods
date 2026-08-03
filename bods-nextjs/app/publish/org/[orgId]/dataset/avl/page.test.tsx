import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AVLPage from './page';
import { useApiResource } from '@/hooks/useApiResource';

const mockUseSearchParams = jest.fn();
let loadFeeds: (() => Promise<unknown>) | undefined;

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useSearchParams: () => mockUseSearchParams(),
  usePathname: () => '/publish/org/123/dataset/avl',
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useApiResource', () => ({
  useApiResource: jest.fn(),
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
  },
}));

jest.mock('@/components/publish/AvlMatchingHelpModal', () => ({
  AvlMatchingHelpModal: () => null,
}));

const mockUseApiResource = useApiResource as jest.Mock;

describe('AVL - Publish - Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    loadFeeds = undefined;
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ count: 0, results: [] }),
    });
    let firstCall = true;
    mockUseApiResource.mockImplementation((loader) => {
      if (firstCall) {
        loadFeeds = loader;
        firstCall = false;
      }
      return { data: { count: 0, results: [] }, isLoading: false, error: '' };
    });
  });

  it.each([
    { tabParam: null, expectedTab: 'active' },
    { tabParam: 'active', expectedTab: 'active' },
    { tabParam: 'draft', expectedTab: 'draft' },
    { tabParam: 'archive', expectedTab: 'archive' },
    { tabParam: 'unexpected', expectedTab: 'active' },
  ])('loads $expectedTab feeds when tab param is $tabParam', async ({ tabParam, expectedTab }) => {
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams(tabParam ? `tab=${tabParam}` : undefined),
    );

    render(<AVLPage />);
    await loadFeeds?.();

    expect(global.fetch).toHaveBeenCalledWith(
      `/api/avl/list/123/?tab=${expectedTab}&sort_by=modified&order=desc&page=1`,
      expect.any(Object),
    );
  });

  it('changes sort order when the same table header is selected twice', async () => {
    let callCount = 0;
    global.fetch = jest.fn().mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ count: 1, results: [] }),
    });
    mockUseApiResource.mockImplementation((loader) => {
      if (callCount % 3 === 0) {
        loadFeeds = loader;
      }
      callCount++;
      return {
        data: {
          count: 1,
          results: [
            {
              id: 456,
              name: 'AVL feed',
              status: 'published',
              percent_matching: null,
              modified: '2026-01-01T00:00:00Z',
              short_description: 'Short description',
            },
          ],
        },
        isLoading: false,
        error: '',
      };
    });

    render(<AVLPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Status' }));
    await loadFeeds?.();

    expect(global.fetch).toHaveBeenLastCalledWith(
      '/api/avl/list/123/?tab=active&sort_by=status&order=asc&page=1',
      expect.any(Object),
    );

    await userEvent.click(screen.getByRole('button', { name: 'Status ▲' }));
    await loadFeeds?.();

    expect(global.fetch).toHaveBeenLastCalledWith(
      '/api/avl/list/123/?tab=active&sort_by=status&order=desc&page=1',
      expect.any(Object),
    );
  });
});