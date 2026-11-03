import { render, screen, within } from '@testing-library/react';
import { publishPath } from '@/config/client';
import { AvlDatasetDetailContent } from './AvlDatasetDetailContent';
import type { AvlDatasetDetail } from './types';

const dataset: AvlDatasetDetail = {
  id: 5,
  name: 'Bus location feed',
  description: 'A description',
  organisationId: 3,
  organisationName: 'Local Import Org',
  status: 'live',
  revisionId: 11,
  lastUpdated: '22 Feb 2026 10:30',
  lastAutomatedUpdate: '23 Feb 2026 08:00',
  siriVmVersion: '2.0',
  avlTimetablesMatching: '85%',
  isSubscribed: false,
  feedApi: null,
};

function renderContent(overrides: Partial<AvlDatasetDetail> = {}) {
  return render(<AvlDatasetDetailContent dataset={{ ...dataset, ...overrides }} />);
}

function rowFor(header: string) {
  return screen.getByRole('rowheader', { name: new RegExp(`^${header}`) }).closest('tr') as HTMLElement;
}

describe('AvlDatasetDetailContent', () => {
  it('renders the Django property table rows in order', () => {
    const { container } = renderContent();

    const headers = Array.from(container.querySelectorAll('table.consumer-property-table th')).map((th) =>
      th.textContent?.trim().replace(/\s+/g, ' '),
    );
    expect(headers.map((header) => header?.slice(0, 28))).toEqual([
      'Name',
      'Data type',
      'Data feed ID',
      'Description',
      'Owner',
      'Status',
      'AVL to Timetables feed match',
      'SIRI-VM version',
      'Feed details last updated',
      'Last automated update',
    ]);
    expect(within(rowFor('Data type')).getByText('Bus location data')).toBeInTheDocument();
    expect(within(rowFor('Data feed ID')).getByText('5')).toBeInTheDocument();
    expect(within(rowFor('SIRI-VM version')).getByText('2.0')).toBeInTheDocument();
    expect(within(rowFor('Feed details last updated')).getByText('22 Feb 2026 10:30')).toBeInTheDocument();
    expect(within(rowFor('Last automated update')).getByText('23 Feb 2026 08:00')).toBeInTheDocument();
  });

  it('links the owner to their live AVL feeds and links the change log', () => {
    renderContent();

    expect(screen.getByRole('link', { name: 'Local Import Org' })).toHaveAttribute(
      'href',
      expect.stringContaining('/avl?organisation=3&status=live'),
    );
    expect(screen.getByRole('link', { name: 'View change log' })).toHaveAttribute(
      'href',
      expect.stringContaining('/avl/dataset/5/changelog'),
    );
  });

  it('shows a warning icon, the score and the matching report link when below 100%', () => {
    const { container } = renderContent({ avlTimetablesMatching: '85%' });
    const row = rowFor('AVL to Timetables feed matching');

    expect(within(row).getByText(/85% completely matched AVL to Timetables/)).toBeInTheDocument();
    expect(row.querySelector('p svg')).not.toBeNull();
    expect(within(row).getByRole('link', { name: 'Download matching report' })).toHaveAttribute(
      'href',
      publishPath('/org/3/dataset/avl/5/download-matching-report/'),
    );
    expect(container.querySelector('.stacked > p.govuk-body.govuk-\\!-margin-bottom-0')).not.toBeNull();
  });

  it('omits the warning icon at 100%', () => {
    renderContent({ avlTimetablesMatching: '100%' });
    const row = rowFor('AVL to Timetables feed matching');

    expect(within(row).getByText(/100% completely matched AVL to Timetables/)).toBeInTheDocument();
    expect(row.querySelector('p svg')).toBeNull();
  });

  it('treats "0%" as a matched score, like the Django template (only null is pending)', () => {
    renderContent({ avlTimetablesMatching: '0%' });

    expect(
      within(rowFor('AVL to Timetables feed matching')).getByText(/0% completely matched/),
    ).toBeInTheDocument();
  });

  it('shows Pending with the icon and no report link while there is no score', () => {
    renderContent({ avlTimetablesMatching: null });
    const row = rowFor('AVL to Timetables feed matching');

    expect(within(row).getByText(/Pending/)).toBeInTheDocument();
    expect(row.querySelector('p svg')).not.toBeNull();
    expect(within(row).queryByRole('link', { name: 'Download matching report' })).not.toBeInTheDocument();
  });

  it('explains the matching score in the help modal', () => {
    renderContent();

    expect(screen.getByText('AVL to Timetables feed sampled matching')).toBeInTheDocument();
    expect(screen.getByText(/This is the latest matching score for this feed\./)).toBeInTheDocument();
  });

  it('hides the API URL panel for anonymous visitors and shows it with the key when signed in', () => {
    const { unmount } = renderContent({ feedApi: null });
    expect(screen.queryByText('Use this data feed in your code')).not.toBeInTheDocument();
    unmount();

    renderContent({
      feedApi: 'https://data.example/api/v1/datafeed/5/?api_key=abc',
    });
    expect(screen.getByRole('heading', { name: 'Use this data feed in your code' })).toBeInTheDocument();
    expect(screen.getByText('https://data.example/api/v1/datafeed/5/?api_key=abc')).toBeInTheDocument();
  });

  it('only offers subscribe (no download) and flips the wording when subscribed', () => {
    const { unmount } = renderContent({ isSubscribed: false });
    expect(screen.getByRole('heading', { name: 'Subscribe' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Subscribe to this data feed' })).toHaveAttribute(
      'href',
      expect.stringContaining('/avl/dataset/5/subscription'),
    );
    expect(screen.queryByText(/Download dataset/)).not.toBeInTheDocument();
    unmount();

    renderContent({ isSubscribed: true });
    expect(screen.getByRole('link', { name: 'Unsubscribe from this data feed' })).toBeInTheDocument();
  });

  it('always shows the data feed feedback link', () => {
    renderContent();

    expect(
      screen.getByRole('heading', {
        name: 'Noticed issues with this data feed?',
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact data feed owner directly' })).toHaveAttribute(
      'href',
      expect.stringContaining('/avl/dataset/5/feedback'),
    );
  });

  it('renders the same content for a non-live status (Django never shows an AVL error panel)', () => {
    renderContent({ status: 'error' });

    expect(screen.queryByText('Data feed not available')).not.toBeInTheDocument();
    expect(screen.getByRole('rowheader', { name: 'SIRI-VM version' })).toBeInTheDocument();
  });
});
