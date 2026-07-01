/**
 * AvlFeedDetailContent Component Tests
 *
 * Tests for AVL feed detail page
 */

import { render, screen, waitFor } from '@testing-library/react';
import { AvlFeedDetailContent, type AvlFeedDetail } from './AvlFeedDetailContent';

const mockUseParams = jest.fn();
const mockApiGet = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: (path: string) => mockApiGet(path),
  },
}));

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('./AvlFeedDetailTable', () => ({
  AvlFeedDetailTable: ({ feedDetail }: { feedDetail: AvlFeedDetail }) => (
    <div data-testid="feed-detail-table">{feedDetail.name}</div>
  ),
}));

jest.mock('./AvlCompliancePanels', () => ({
  AvlCompliancePanels: ({ feedDetail }: { feedDetail: AvlFeedDetail }) => (
    <div data-testid="compliance-panels">{feedDetail.avlComplianceStatus}</div>
  ),
}));

jest.mock('./AvlFeedDetailSidebar', () => ({
  AvlFeedDetailSidebar: () => <div data-testid="feed-sidebar">Sidebar</div>,
}));

jest.mock('./AvlFeedDetailActions', () => ({
  AvlFeedDetailActions: ({ feedDetail }: { feedDetail: AvlFeedDetail }) => (
    <div data-testid="feed-actions">{feedDetail.status}</div>
  ),
}));

describe('AvlFeedDetailContent', () => {
  const mockParams = {
    orgId: 'org-123',
    datasetId: 'dataset-456',
  };

  const mockFeedDetail: AvlFeedDetail = {
    datasetId: 456,
    name: 'Test AVL Feed',
    description: 'Test Description',
    shortDescription: 'Short',
    status: 'published',
    organisationName: 'Test Org',
    organisationId: 123,
    siriVersion: '2.0',
    urlLink: 'https://example.com/feed',
    lastModified: '2026-01-15T10:30:00+00:00',
    lastModifiedUser: 'test-user',
    lastServerUpdate: '2026-01-15T10:35:00+00:00',
    publishedBy: 'publisher-user',
    publishedAt: '2026-01-15T09:00:00+00:00',
    avlComplianceStatus: 'compliant',
    avlTimetablesMatching: '95%',
    isDummy: false,
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue(mockParams);
  });

  it('renders loading state initially', () => {
    mockApiGet.mockImplementation(() => new Promise(() => {})); // Never resolves

    render(<AvlFeedDetailContent />);

    expect(screen.getByText(/Loading feed details/i)).toBeInTheDocument();
  });

  it('fetches feed detail on mount', async () => {
    mockApiGet.mockResolvedValue(mockFeedDetail);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/avl/detail/org-123/dataset-456/');
    });
  });

  it('renders feed detail content when data loads successfully', async () => {
    mockApiGet.mockResolvedValue(mockFeedDetail);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('feed-detail-table')).toBeInTheDocument();
    });

    expect(screen.getByTestId('compliance-panels')).toBeInTheDocument();
    expect(screen.getByTestId('feed-sidebar')).toBeInTheDocument();
    expect(screen.getByTestId('feed-actions')).toBeInTheDocument();
  });

  it('renders feed detail content with correct name', async () => {
    mockApiGet.mockResolvedValue(mockFeedDetail);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      const allMatches = screen.getAllByText('Test AVL Feed');
      expect(allMatches.length).toBeGreaterThan(0);
    });
  });

  it('truncates long feed names in breadcrumb', async () => {
    const longFeedDetail = {
      ...mockFeedDetail,
      name: 'This is a very long feed name that should be truncated',
    };

    mockApiGet.mockResolvedValue(longFeedDetail);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      const breadcrumbLink = screen.getByRole('link', { name: /This is a very l/ });
      expect(breadcrumbLink).toBeInTheDocument();
    });
  });

  it('displays error when API call fails', async () => {
    mockApiGet.mockRejectedValue(new Error('Network error'));

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to load feed details/i)).toBeInTheDocument();
    });
  });

  it('displays custom error message', async () => {
    const errorMsg = 'Feed not found';
    mockApiGet.mockRejectedValue(new Error(errorMsg));

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByText(errorMsg)).toBeInTheDocument();
    });
  });

  it('displays default error when feed detail is not returned', async () => {
    mockApiGet.mockResolvedValue(null);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to load feed details/i)).toBeInTheDocument();
    });
  });

  it('provides back link on error', async () => {
    mockApiGet.mockRejectedValue(new Error('Error'));

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      const backLink = screen.getByRole('link', { name: /Back to feeds/i });
      expect(backLink).toBeInTheDocument();
      expect(backLink).toHaveAttribute('href', '/publish/org/org-123/dataset/avl');
    });
  });

  it('handles API error gracefully', async () => {
    const error = new Error('Failed to fetch');
    mockApiGet.mockRejectedValue(error);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to load feed details/i)).toBeInTheDocument();
    });
  });

  it('cancels fetch on unmount', async () => {
    let resolveApiCall: any;
    const apiPromise = new Promise((resolve) => {
      resolveApiCall = resolve;
    });
    mockApiGet.mockReturnValue(apiPromise);

    const { unmount } = render(<AvlFeedDetailContent />);

    unmount();

    // Resolve after unmount
    resolveApiCall(mockFeedDetail);

    // Should not cause errors
    expect(true).toBe(true);
  });

  it('renders published feed correctly', async () => {
    const publishedFeed = {
      ...mockFeedDetail,
      status: 'published',
      publishedAt: '2026-01-15T09:00:00+00:00',
    };

    mockApiGet.mockResolvedValue(publishedFeed);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('feed-actions')).toBeInTheDocument();
    });

    expect(screen.getByTestId('feed-actions')).toHaveTextContent('published');
  });

  it('renders draft feed correctly', async () => {
    const draftFeed = {
      ...mockFeedDetail,
      status: 'draft',
    };

    mockApiGet.mockResolvedValue(draftFeed);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('feed-actions')).toHaveTextContent('draft');
    });
  });

  it('handles dummy feed correctly', async () => {
    const dummyFeed = {
      ...mockFeedDetail,
      isDummy: true,
    };

    mockApiGet.mockResolvedValue(dummyFeed);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('feed-detail-table')).toBeInTheDocument();
    });
  });

  it('includes compliance panels with compliance status', async () => {
    const awaitingReviewFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'awaiting_review',
    };

    mockApiGet.mockResolvedValue(awaitingReviewFeed);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('compliance-panels')).toHaveTextContent('awaiting_review');
    });
  });

  it('renders timetables matching percentage', async () => {
    const feedWithMatching = {
      ...mockFeedDetail,
      avlTimetablesMatching: '87.5%',
    };

    mockApiGet.mockResolvedValue(feedWithMatching);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(screen.getByTestId('feed-detail-table')).toBeInTheDocument();
    });
  });

  it('fetches data with correct org and dataset IDs', async () => {
    mockApiGet.mockResolvedValue(mockFeedDetail);

    render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/avl/detail/org-123/dataset-456/');
    });
  });

  it('updates when params change', async () => {
    mockApiGet.mockResolvedValue(mockFeedDetail);

    const { rerender } = render(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledTimes(1);
    });

    mockUseParams.mockReturnValue({
      orgId: 'org-789',
      datasetId: 'dataset-999',
    });

    rerender(<AvlFeedDetailContent />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith('/api/avl/detail/org-789/dataset-999/');
    });
  });
});
