/**
 * DatasetList Component Tests
 * 
 */

import { render, screen, waitFor } from '@testing-library/react';
import { DatasetList } from './DatasetList';
import type { DatasetListItem, PaginatedResponse } from '@/types';

const mockPush = jest.fn();
const mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  usePathname: () => '/data',
  useSearchParams: () => mockSearchParams,
}));

global.fetch = jest.fn();

jest.mock('./DatasetCard', () => ({
  DatasetCard: ({ dataset }: { dataset: DatasetListItem }) => (
    <div data-testid={`dataset-card-${dataset.id}`}>{dataset.name}</div>
  ),
}));

jest.mock('@/components/shared/LoadingSpinner', () => ({
  LoadingSpinner: ({ message }: { message: string }) => (
    <div data-testid="loading-spinner">{message}</div>
  ),
}));

jest.mock('@/components/shared/ErrorDisplay', () => ({
  ErrorDisplay: ({ message, onRetry }: { message: string; onRetry?: () => void }) => (
    <div data-testid="error-display">
      <span>{message}</span>
      {onRetry && <button onClick={onRetry}>Try again</button>}
    </div>
  ),
}));

jest.mock('@/components/shared/Pagination', () => ({
  Pagination: ({ currentPage, totalPages }: { currentPage: number; totalPages: number }) => (
    <nav data-testid="pagination">
      Page {currentPage} of {totalPages}
    </nav>
  ),
}));

describe('DatasetList', () => {
  const mockDatasets: DatasetListItem[] = [
    {
      id: 1,
      name: 'Dataset One',
      operatorName: 'Operator One',
      description: 'Description one',
      status: 'published',
      modified: '2026-01-15T10:00:00+00:00',
      dqScore: '90.0%',
      dqRag: 'green',
      dataType: 'TIMETABLE',
    },
    {
      id: 2,
      name: 'Dataset Two',
      operatorName: 'Operator Two',
      description: 'Description two',
      status: 'published',
      modified: '2026-01-14T10:00:00+00:00',
      dqScore: '75.0%',
      dqRag: 'amber',
      dataType: 'TIMETABLE',
    },
  ];

  const mockPaginatedResponse: PaginatedResponse<DatasetListItem> = {
    count: 42,
    next: 'http://example.com/api/v1/dataset/?limit=20&offset=20',
    previous: null,
    results: mockDatasets,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams.delete('page');
  });

  describe('with initial data', () => {
    it('renders dataset cards from initial data', () => {
      render(<DatasetList initialData={mockPaginatedResponse} />);
      
      expect(screen.getByTestId('dataset-card-1')).toBeInTheDocument();
      expect(screen.getByTestId('dataset-card-2')).toBeInTheDocument();
    });

    it('displays total count', () => {
      render(<DatasetList initialData={mockPaginatedResponse} />);
      
      expect(screen.getByText(/42 datasets found/i)).toBeInTheDocument();
    });

    it('renders pagination when more than one page', () => {
      render(<DatasetList initialData={mockPaginatedResponse} pageSize={20} />);
      
      expect(screen.getByTestId('pagination')).toBeInTheDocument();
    });

    it('does not render pagination for single page', () => {
      const singlePageData: PaginatedResponse<DatasetListItem> = {
        ...mockPaginatedResponse,
        count: 5,
        next: null,
      };
      
      render(<DatasetList initialData={singlePageData} pageSize={20} />);
      
      expect(screen.queryByTestId('pagination')).not.toBeInTheDocument();
    });
  });

  describe('without initial data', () => {
    it('shows loading spinner initially', () => {
      (global.fetch as jest.Mock).mockImplementation(() => new Promise(() => {}));
      
      render(<DatasetList />);
      
      expect(screen.getByTestId('loading-spinner')).toBeInTheDocument();
    });

    it('fetches data from API', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });
      
      render(<DatasetList />);
      
      await waitFor(() => {
        expect(global.fetch).toHaveBeenCalledWith(
          expect.stringContaining('/api/v1/dataset/'),
          expect.objectContaining({
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
          })
        );
      });
    });

    it('displays datasets after successful fetch', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockPaginatedResponse),
      });
      
      render(<DatasetList />);
      
      await waitFor(() => {
        expect(screen.getByTestId('dataset-card-1')).toBeInTheDocument();
      });
    });
  });

  describe('error handling', () => {
    it('displays error when fetch fails', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 500,
        statusText: 'Internal Server Error',
      });
      
      render(<DatasetList />);
      
      await waitFor(() => {
        expect(screen.getByTestId('error-display')).toBeInTheDocument();
      });
    });

    it('displays authentication error for 401 response', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        status: 401,
        statusText: 'Unauthorized',
      });
      
      render(<DatasetList />);
      
      await waitFor(() => {
        expect(screen.getByText(/authentication required/i)).toBeInTheDocument();
      });
    });

    it('allows retry after error', async () => {
      (global.fetch as jest.Mock)
        .mockResolvedValueOnce({
          ok: false,
          status: 500,
          statusText: 'Internal Server Error',
        })
        .mockResolvedValueOnce({
          ok: true,
          json: () => Promise.resolve(mockPaginatedResponse),
        });
      
      render(<DatasetList />);
      
      await waitFor(() => {
        expect(screen.getByTestId('error-display')).toBeInTheDocument();
      });
      
      const retryButton = screen.getByRole('button', { name: /try again/i });
      retryButton.click();
      
      await waitFor(() => {
        expect(screen.getByTestId('dataset-card-1')).toBeInTheDocument();
      });
    });
  });

  describe('empty state', () => {
    it('displays empty message when no datasets', () => {
      const emptyResponse: PaginatedResponse<DatasetListItem> = {
        count: 0,
        next: null,
        previous: null,
        results: [],
      };
      
      render(<DatasetList initialData={emptyResponse} />);
      
      expect(screen.getByText(/no datasets found/i)).toBeInTheDocument();
    });
  });

  describe('accessibility', () => {
    it('has proper list semantics', () => {
      render(<DatasetList initialData={mockPaginatedResponse} />);
      
      const list = screen.getByRole('list', { name: /dataset results/i });
      expect(list).toBeInTheDocument();
      
      const items = screen.getAllByRole('listitem');
      expect(items).toHaveLength(2);
    });

    it('announces results count to screen readers', () => {
      render(<DatasetList initialData={mockPaginatedResponse} />);
      
      const announcement = screen.getByText(/42 datasets found/i).closest('[aria-live]');
      expect(announcement).toHaveAttribute('aria-live', 'polite');
    });
  });
});

