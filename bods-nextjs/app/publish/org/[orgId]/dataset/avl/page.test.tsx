import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AVLPage from './page';
import { api } from '@/lib/api-client';
import { useApiResource } from '@/hooks/useApiResource';

const mockUseSearchParams = jest.fn();
let loadFeeds: (() => Promise<unknown>) | undefined;

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useSearchParams: () => mockUseSearchParams(),
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
    (api.get as jest.Mock).mockResolvedValue({ count: 0, results: [] });
    mockUseApiResource.mockImplementation((loader) => {
      loadFeeds = loader;
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

    expect(api.get).toHaveBeenCalledWith(
      `/api/avl/list/123?tab=${expectedTab}&sort_by=modified&order=desc`,
    );
  });

  it('changes sort order when the same table header is selected twice', async () => {
    mockUseApiResource.mockImplementation((loader) => {
      loadFeeds = loader;
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

    expect(api.get).toHaveBeenLastCalledWith(
      '/api/avl/list/123?tab=active&sort_by=status&order=desc',
    );

    await userEvent.click(screen.getByRole('button', { name: 'Status ▼' }));
    await loadFeeds?.();

    expect(api.get).toHaveBeenLastCalledWith(
      '/api/avl/list/123?tab=active&sort_by=status&order=asc',
    );
  });
});