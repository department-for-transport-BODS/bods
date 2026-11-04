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

    const href = screen.getByRole('button', { name: /Update data feed/i }).getAttribute('href');
    expect(href).toMatch(/\/org\/org-123\/dataset\/avl\/dataset-456\/update\/$/);
    expect(href).not.toMatch(/\/publish\/org/);
  });

  it('links to the Django deactivate URL', () => {
    render(
      <AvlFeedDetailActions
        feedDetail={mockFeedDetail}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const href = screen.getByRole('button', { name: /Deactivate data feed/i }).getAttribute('href');
    expect(href).toMatch(/\/org\/org-123\/dataset\/avl\/dataset-456\/deactivate\/$/);
    expect(href).not.toMatch(/\/publish\/org/);
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

  it.each(['success', 'indexing', 'pending'])(
    'renders both buttons linking to update and deactivate for %s status',
    (status) => {
      render(
        <AvlFeedDetailActions
          feedDetail={{ ...mockFeedDetail, status }}
          orgId="org-123"
          datasetId="dataset-456"
        />
      );

      expect(screen.getByRole('button', { name: /Update data feed/i }).getAttribute('href')).toMatch(
        /\/update\/$/
      );
      expect(screen.getByRole('button', { name: /Deactivate data feed/i })).toBeInTheDocument();
    }
  );

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
});
