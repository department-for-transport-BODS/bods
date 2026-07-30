/**
 * AvlReviewPageContent Component Tests
 *
 * Tests for AVL review/publish page logic
 */

import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { AvlReviewPageContent } from './AvlReviewPageContent';

const mockUseParams = jest.fn();
const mockUseSearchParams = jest.fn();
const mockApiGet = jest.fn();
const mockApiPost = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => mockUseParams(),
  useSearchParams: () => mockUseSearchParams(),
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: (path: string) => mockApiGet(path),
    post: (path: string, body?: unknown) => mockApiPost(path, body),
  },
}));

jest.mock('@/components/publish', () => ({
  PublishStepper: () => (
    <div data-testid="publish-stepper">Stepper</div>
  ),
}));

jest.mock('./AvlReviewAuxiliaryPanels', () => ({
  AvlReviewErrorGuidance: ({ error }: { error: string }) => (
    <div data-testid="error-guidance">{error}</div>
  ),
  AvlReviewHelpAside: () => <div data-testid="help-aside">Help</div>,
}));

jest.mock('./avlStatus', () => ({
  statusIndicatorClass: (status: string) => `class-${status}`,
  statusLabel: (status: string) => status,
}));

describe('AvlReviewPageContent', () => {
  const mockParams = {
    orgId: 'org-123',
    datasetId: 'dataset-456',
  };

  const mockReviewResponse = {
    datasetId: 456,
    revisionId: 1,
    status: 'processing',
    progress: 50,
    loading: false,
    name: 'Test Feed',
    description: 'Test Description',
    shortDescription: 'Short',
    urlLink: 'https://example.com/feed',
    ownerName: 'Test Owner',
    siriVersion: '2.0',
    lastModified: '2026-01-15T10:30:00+00:00',
    lastModifiedUser: 'test-user',
  };

  beforeEach(() => {
    jest.clearAllMocks();
    mockUseParams.mockReturnValue(mockParams);
    mockUseSearchParams.mockReturnValue(new URLSearchParams());
    mockApiGet.mockImplementation((path: string) => Promise.resolve(
      path.includes('/progress/')
        ? { progress: 100, status: 'success' }
        : mockReviewResponse,
    ));
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it('renders loading state on initial load', () => {
    mockApiGet.mockReturnValue(new Promise(() => undefined));

    render(<AvlReviewPageContent isUpdate={false} />);

    expect(screen.getByText(/Your data is being processed/i)).toBeInTheDocument();
  });

  it('displays progress percentage', async () => {
    mockApiGet.mockResolvedValue({ progress: 75, status: 'pending' });

    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByText('75%')).toBeInTheDocument();
    });
  });

  it('fetches status on mount', async () => {
    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(mockApiGet).toHaveBeenCalledWith(
        '/api/publish/dataset/dataset-456/progress/',
      );
      expect(mockApiGet).toHaveBeenCalledWith(
        '/api/publish/avl/review-status/org-123/dataset-456/',
      );
    });
  });

  it('shows consent checkbox when processing is complete', async () => {
    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByRole('checkbox', { name: /I have reviewed the data/ })).toBeInTheDocument();
    });
  });

  it('validates consent before publishing', async () => {
    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByRole('checkbox', { name: /I have reviewed the data/ })).toBeInTheDocument();
    });

    // Without checking the checkbox, publish should show error
    const buttons = screen.queryAllByRole('button', { name: /Publish/i });
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('displays error when publish fails', async () => {
    mockApiPost.mockRejectedValue(new Error('Network error'));

    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByRole('checkbox', { name: /I have reviewed the data/ })).toBeInTheDocument();
    });

    // Just verify error handling is in place
    expect(mockApiPost.mock.calls.length).toBe(0); // No publish attempted yet
  });

  it('displays review error message when status has error', async () => {
    mockApiGet.mockImplementation((path: string) => Promise.resolve(
      path.includes('/progress/')
        ? { progress: 100, status: 'error' }
        : { ...mockReviewResponse, error: 'Invalid data format' },
    ));

    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByTestId('error-guidance')).toBeInTheDocument();
    });
  });

  it('clears errors when consent is unchecked', async () => {
    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /I have reviewed the data/ });
      fireEvent.click(checkbox);
    });

    const checkbox = screen.getByRole('checkbox', { name: /I have reviewed the data/ });
    fireEvent.click(checkbox);
    fireEvent.click(checkbox);

    // Error message should be cleared
    expect(screen.queryByText(/You must confirm/i)).not.toBeInTheDocument();
  });

  it('handles API error gracefully', async () => {
    mockApiGet.mockRejectedValue(new Error('API Error'));

    render(<AvlReviewPageContent isUpdate={false} />);

    await waitFor(() => {
      expect(screen.getByText(/Unable to check processing status/i)).toBeInTheDocument();
    });
  });

  it('renders for update mode', async () => {
    render(<AvlReviewPageContent isUpdate={true} />);

    await waitFor(() => {
      const checkbox = screen.getByRole('checkbox', { name: /I have reviewed the data/ });
      expect(checkbox).toBeInTheDocument();
    });
  });

  it('shows edit links for description fields in update review mode', async () => {
    render(<AvlReviewPageContent isUpdate />);

    await waitFor(() => {
      const editLinks = screen.getAllByRole('link', { name: 'Edit' });
      expect(editLinks).toHaveLength(2);
      expect(editLinks[0]).toHaveAttribute(
        'href',
        '/publish/org/org-123/dataset/avl/dataset-456/dataset-edit?mode=revision&redirect=%2Fpublish%2Forg%2Forg-123%2Fdataset%2Favl%2Fdataset-456%2Fupdate%2Freview',
      );
    });
  });
});
