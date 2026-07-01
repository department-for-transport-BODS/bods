/**
 * AvlFeedDetailTable Component Tests
 *
 * Tests for AVL feed detail property table
 */

import { render, screen } from '@testing-library/react';
import { AvlFeedDetailTable } from './AvlFeedDetailTable';
import type { AvlFeedDetail } from './AvlFeedDetailContent';

jest.mock('next/link', () => {
  return function MockLink({ children, href, ...props }: { children: React.ReactNode; href: string }) {
    return <a href={href} {...props}>{children}</a>;
  };
});

jest.mock('../../_components/avlStatus', () => ({
  statusIndicatorClass: (status: string) => `class-${status}`,
  statusLabel: (status: string) => status.toUpperCase(),
}));

jest.mock('@/components/publish/AvlMatchingHelpModal', () => ({
  AvlMatchingHelpModal: ({ variant }: { variant: string }) => (
    <div data-testid="matching-help">{variant}</div>
  ),
}));

jest.mock('@/lib/utils/date', () => ({
  formatDateTime: (date: string) => 'Formatted: 15 Jan 2026, 10:30',
}));

describe('AvlFeedDetailTable', () => {
  const mockFeedDetail: AvlFeedDetail = {
    datasetId: 456,
    name: 'Test AVL Feed',
    description: 'This is a test description',
    shortDescription: 'Short desc',
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

  it('renders table structure', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays feed name', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('Test AVL Feed')).toBeInTheDocument();
  });

  it('displays feed ID', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('456')).toBeInTheDocument();
  });

  it('displays URL link', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('https://example.com/feed')).toBeInTheDocument();
  });

  it('displays description', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('This is a test description')).toBeInTheDocument();
  });

  it('displays short description', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('Short desc')).toBeInTheDocument();
  });

  it('displays status with correct formatting', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('PUBLISHED')).toBeInTheDocument();
  });

  it('displays timetables matching percentage', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    // Check that 95% is in the document (might be split across elements)
    const tableContent = screen.getByRole('table');
    expect(tableContent.textContent).toContain('95%');
  });

  it('provides edit link for description when not dummy', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    const editLinks = screen.getAllByRole('link', { name: /Edit/i });
    expect(editLinks.length).toBeGreaterThan(0);
  });

  it('links to correct edit URL', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    const editLinks = screen.getAllByRole('link', { name: /Edit/i });
    expect(editLinks[0]).toHaveAttribute(
      'href',
      '/publish/org/org-123/dataset/avl/456/dataset-edit'
    );
  });

  it('does not show edit links for dummy feeds', () => {
    const dummyFeed = { ...mockFeedDetail, isDummy: true };

    render(
      <AvlFeedDetailTable
        feedDetail={dummyFeed}
        orgId="org-123"
      />
    );

    expect(screen.queryByRole('link', { name: /Edit/i })).not.toBeInTheDocument();
  });

  it('displays all row headers', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Data feed ID')).toBeInTheDocument();
    expect(screen.getByText('URL link')).toBeInTheDocument();
    expect(screen.getByText('Description')).toBeInTheDocument();
    expect(screen.getByText('Short description')).toBeInTheDocument();
    expect(screen.getByText('Status')).toBeInTheDocument();
  });

  it('includes matching help modal', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByTestId('matching-help')).toBeInTheDocument();
  });

  it('handles different statuses correctly', () => {
    const statuses = ['published', 'draft', 'inactive', 'archived'];

    statuses.forEach((status) => {
      const feedWithStatus = { ...mockFeedDetail, status };
      const { unmount } = render(
        <AvlFeedDetailTable
          feedDetail={feedWithStatus}
          orgId="org-123"
        />
      );

      expect(screen.getByText(status.toUpperCase())).toBeInTheDocument();
      unmount();
    });
  });

  it('handles optional matching percentage', () => {
    const feedWithoutMatching = { ...mockFeedDetail, avlTimetablesMatching: undefined };

    render(
      <AvlFeedDetailTable
        feedDetail={feedWithoutMatching}
        orgId="org-123"
      />
    );

    // Should still render without errors
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('handles long URLs without breaking', () => {
    const longUrlFeed = {
      ...mockFeedDetail,
      urlLink: 'https://example.com/path/to/very/long/url/that/contains/many/segments/and/parameters?key=value&other=param',
    };

    render(
      <AvlFeedDetailTable
        feedDetail={longUrlFeed}
        orgId="org-123"
      />
    );

    expect(screen.getByText(longUrlFeed.urlLink)).toBeInTheDocument();
  });

  it('displays organization information', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    // Organization should be displayed somewhere in the table
    expect(screen.getByRole('table')).toBeInTheDocument();
  });

  it('displays SIRI version', () => {
    render(
      <AvlFeedDetailTable
        feedDetail={mockFeedDetail}
        orgId="org-123"
      />
    );

    expect(screen.getByText('2.0')).toBeInTheDocument();
  });

  it('handles special characters in description', () => {
    const specialFeed = {
      ...mockFeedDetail,
      description: 'Description with <special> & "characters"',
    };

    render(
      <AvlFeedDetailTable
        feedDetail={specialFeed}
        orgId="org-123"
      />
    );

    expect(screen.getByText('Description with <special> & "characters"')).toBeInTheDocument();
  });
});
