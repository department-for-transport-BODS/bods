/**
 * AvlCompliancePanels Component Tests
 *
 * Tests for AVL feed compliance status panels
 */

import { render, screen } from '@testing-library/react';
import { AvlCompliancePanels } from './AvlCompliancePanels';
import type { AvlFeedDetail } from './AvlFeedDetailContent';

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

describe('AvlCompliancePanels', () => {
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

  it('renders nothing for compliant status', () => {
    const compliantFeed = { ...mockFeedDetail, avlComplianceStatus: 'Compliant' };

    const { container } = render(
      <AvlCompliancePanels
        feedDetail={compliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders warning panel for awaiting review status', () => {
    const awaitingReviewFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Awaiting publisher review',
      status: 'published',
    };

    render(
      <AvlCompliancePanels
        feedDetail={awaitingReviewFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByText(/Your data is currently being published but contains potential issues/i)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: /Download validation report/i })).toBeInTheDocument();
  });

  it('includes unpublish warning for draft status with awaiting review', () => {
    const awaitingReviewDraftFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Awaiting publisher review',
      status: 'draft',
    };

    render(
      <AvlCompliancePanels
        feedDetail={awaitingReviewDraftFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByText(/If no corrections are made your feed will be unpublished/i)).toBeInTheDocument();
  });

  it('does not include unpublish warning for published status with awaiting review', () => {
    const awaitingReviewPublishedFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Awaiting publisher review',
      status: 'published',
    };

    render(
      <AvlCompliancePanels
        feedDetail={awaitingReviewPublishedFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.queryByText(/If no corrections are made your feed will be unpublished/i)).not.toBeInTheDocument();
  });

  it('renders warning panel for partially compliant status', () => {
    const partiallyCompliantFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Partially compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={partiallyCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByText(/The AVL data feed is only partially compliant/i)).toBeInTheDocument();
    expect(screen.getByText(/To fully pass validation please address all outstanding issues/i)).toBeInTheDocument();
  });

  it('includes validation report link for partially compliant', () => {
    const partiallyCompliantFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Partially compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={partiallyCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const link = screen.getByRole('link', { name: /Download validation report/i });
    expect(link).toHaveAttribute('href', '/api/avl/download-validation-report/456');
  });

  it('renders error panel for non-compliant status', () => {
    const nonCompliantFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Non-compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={nonCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByText('Data feed not compliant')).toBeInTheDocument();
    expect(screen.getByText(/The AVL data feed is non-compliant/i)).toBeInTheDocument();
  });

  it('includes validation report link for non-compliant', () => {
    const nonCompliantFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Non-compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={nonCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const link = screen.getByRole('link', { name: /Download validation report/i });
    expect(link).toHaveAttribute('href', '/api/avl/download-validation-report/456');
  });

  it('uses correct validation report URL with dataset ID', () => {
    const nonCompliantFeed = {
      ...mockFeedDetail,
      datasetId: 789,
      avlComplianceStatus: 'Non-compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={nonCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    const link = screen.getByRole('link', { name: /Download validation report/i });
    expect(link).toHaveAttribute('href', '/api/avl/download-validation-report/789');
  });

  it('renders nothing for unknown compliance status', () => {
    const unknownStatusFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Unknown Status' as any,
    };

    const { container } = render(
      <AvlCompliancePanels
        feedDetail={unknownStatusFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(container.firstChild).toBeNull();
  });

  it('renders warning text with correct ARIA label for awaiting review', () => {
    const awaitingReviewFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Awaiting publisher review',
    };

    render(
      <AvlCompliancePanels
        feedDetail={awaitingReviewFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByText('Warning')).toBeInTheDocument();
  });

  it('renders error role for non-compliant status', () => {
    const nonCompliantFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'Non-compliant',
    };

    render(
      <AvlCompliancePanels
        feedDetail={nonCompliantFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('handles case sensitive status values', () => {
    const caseSensitiveFeed = {
      ...mockFeedDetail,
      avlComplianceStatus: 'compliant', // lowercase
    };

    const { container } = render(
      <AvlCompliancePanels
        feedDetail={caseSensitiveFeed}
        orgId="org-123"
        datasetId="dataset-456"
      />
    );

    // Component only matches exact casing - lowercase 'compliant' renders nothing
    expect(container.firstChild).toBeNull();
  });
});
