/**
 * AvlFeedDetailActions Component Tests
 *
 * Tests for AVL feed detail action buttons
 */

import { render, screen } from '@testing-library/react';
import { AvlFeedDetailActions } from './AvlFeedDetailActions';
import type { AvlFeedDetail } from './AvlFeedDetailContent';

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('AvlFeedDetailActions', () => {
  const mockFeedDetail: AvlFeedDetail = {
    datasetId: 456,
    name: 'Test Feed',
    description: 'Test',
    shortDescription: 'Short',
    status: 'published',
    organisationName: 'Org',
    organisationId: 123,
    siriVersion: '2.0',
    urlLink: 'https://example.com',
    lastModified: '2026-01-15T10:30:00+00:00',
    lastServerUpdate: '2026-01-15T10:35:00+00:00',
    publishedAt: '2026-01-15T09:00:00+00:00',
    avlComplianceStatus: 'compliant',
    isDummy: false,
  };

  it('renders update and deactivate buttons for published feeds', () => {
    render(
      <AvlFeedDetailActions
        feedDetail={mockFeedDetail}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const updateButton = screen.getByRole('button', { name: /Update data feed/i });
    const deactivateButton = screen.getByRole('button', { name: /Deactivate data feed/i });

    expect(updateButton).toBeInTheDocument();
    expect(deactivateButton).toBeInTheDocument();
  });

  it('links to correct update URL', () => {
    render(
      <AvlFeedDetailActions
        feedDetail={mockFeedDetail}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const updateButton = screen.getByRole('button', { name: /Update data feed/i });
    expect(updateButton).toHaveAttribute(
      'href',
      '/publish/org/org-123/dataset/avl/dataset-456/update'
    );
  });

  it('links to correct deactivate URL with feed name', () => {
    render(
      <AvlFeedDetailActions
        feedDetail={mockFeedDetail}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const deactivateButton = screen.getByRole('button', { name: /Deactivate data feed/i });
    expect(deactivateButton).toHaveAttribute(
      'href',
      '/publish/org/org-123/dataset/avl/dataset-456/archive?name=Test%20Feed'
    );
  });

  it('does not render buttons for dummy feeds', () => {
    const dummyFeed = { ...mockFeedDetail, isDummy: true };

    render(
      <AvlFeedDetailActions
        feedDetail={dummyFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.queryByRole('button', { name: /Update data feed/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Deactivate data feed/i })).not.toBeInTheDocument();
  });

  it('does not render buttons for inactive feeds', () => {
    const inactiveFeed = { ...mockFeedDetail, status: 'inactive' };

    render(
      <AvlFeedDetailActions
        feedDetail={inactiveFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.queryByRole('button', { name: /Update data feed/i })).not.toBeInTheDocument();
    expect(screen.queryByRole('button', { name: /Deactivate data feed/i })).not.toBeInTheDocument();
  });

  it('only shows deactivate button for expired feeds', () => {
    const expiredFeed = { ...mockFeedDetail, status: 'expired' };

    render(
      <AvlFeedDetailActions
        feedDetail={expiredFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const updateButton = screen.getByRole('button', { name: /Update data feed/i });
    const deactivateButton = screen.queryByRole('button', { name: /Deactivate data feed/i });

    expect(updateButton).toBeInTheDocument();
    expect(deactivateButton).not.toBeInTheDocument();
  });

  it('handles feed names with special characters in URL', () => {
    const specialFeed = { ...mockFeedDetail, name: 'Feed & Event (2026)' };

    render(
      <AvlFeedDetailActions
        feedDetail={specialFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const deactivateButton = screen.getByRole('button', { name: /Deactivate data feed/i });
    expect(deactivateButton).toHaveAttribute('href', expect.stringContaining('name='));
  });

  it('renders buttons with correct CSS classes', () => {
    render(
      <AvlFeedDetailActions
        feedDetail={mockFeedDetail}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const updateButton = screen.getByRole('button', { name: /Update data feed/i });
    const deactivateButton = screen.getByRole('button', { name: /Deactivate data feed/i });

    expect(updateButton).toHaveClass('govuk-button');
    expect(deactivateButton).toHaveClass('govuk-button');
    expect(deactivateButton).toHaveClass('govuk-button--secondary');
  });

  it('renders update button for draft feeds', () => {
    const draftFeed = { ...mockFeedDetail, status: 'draft' };

    render(
      <AvlFeedDetailActions
        feedDetail={draftFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByRole('button', { name: /Update data feed/i })).toBeInTheDocument();
  });

  it('renders both buttons for awaiting review feeds', () => {
    const awaitingReviewFeed = { ...mockFeedDetail, status: 'awaiting_review' };

    render(
      <AvlFeedDetailActions
        feedDetail={awaitingReviewFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByRole('button', { name: /Update data feed/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Deactivate data feed/i })).toBeInTheDocument();
  });

  it('handles long feed names correctly in URL encoding', () => {
    const longNameFeed = {
      ...mockFeedDetail,
      name: 'This is a very long feed name that contains spaces and should be encoded properly',
    };

    render(
      <AvlFeedDetailActions
        feedDetail={longNameFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const deactivateButton = screen.getByRole('button', { name: /Deactivate data feed/i });
    const href = deactivateButton.getAttribute('href');

    expect(href).toContain('archive');
    expect(href).toContain('name=');
    expect(href).not.toContain(' '); // Spaces should be encoded
  });
});
