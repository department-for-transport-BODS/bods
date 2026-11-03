import { fireEvent, render, screen, within } from '@testing-library/react';
import { TimetableDatasetDetailContent } from './TimetableDatasetDetailContent';
import { DatasetStatusIndicator } from './DatasetStatusIndicator';
import { DatasetDetailLayout } from './DatasetDetailLayout';
import { DatasetFeedbackSection } from './DatasetFeedbackSection';
import { DatasetApiUrlPanel } from './DatasetApiUrlPanel';
import type { TimetableDatasetDetail } from './types';

jest.mock('@/components/data/MapboxRouteMap', () => ({
  MapboxRouteMap: ({ revisionId }: { revisionId: number }) => <div data-testid="map" data-revision={revisionId} />,
}));

const dataset: TimetableDatasetDetail = {
  id: 1,
  name: 'Local Import Org_unknown_530',
  description: 'A description',
  organisationId: 5,
  organisationName: 'Local Import Org',
  status: 'live',
  revisionId: 11,
  transxchangeVersion: '2.4',
  uploadFileExtension: 'zip',
  lastUpdated: '22 Feb 2026 10:30',
  publishedBy: null,
  error: false,
  dataQuality: null,
  isSubscribed: false,
  feedApi: null,
  serviceNumbers: [
    {
      licenceNumber: 'PB0000001',
      nocs: [
        {
          noc: 'NOC1',
          lines: [
            { lineName: '14', serviceCodes: ['PB1:14', 'PB2:14'] },
            { lineName: '15', serviceCodes: ['PB1:15'] },
          ],
        },
      ],
    },
  ],
};

function renderContent(overrides: Partial<TimetableDatasetDetail> = {}, isSpecificFeedback = false) {
  return render(
    <TimetableDatasetDetailContent dataset={{ ...dataset, ...overrides }} isSpecificFeedback={isSpecificFeedback} />,
  );
}

function rowFor(header: string) {
  return screen.getByRole('rowheader', { name: new RegExp(`^${header}`) }).closest('tr') as HTMLElement;
}

describe('TimetableDatasetDetailContent (success)', () => {
  it('renders the Django property table rows in order', () => {
    const { container } = renderContent();

    const headers = Array.from(container.querySelectorAll('table.consumer-property-table th')).map((th) =>
      th.textContent?.trim(),
    );
    expect(headers).toEqual([
      'Name',
      'Data type',
      'Data set ID',
      'Description',
      'Owner',
      'Status',
      'TransXChange version',
      'Last updated',
    ]);
    expect(within(rowFor('Data type')).getByText('Timetables data')).toBeInTheDocument();
    expect(within(rowFor('Data set ID')).getByText('1')).toBeInTheDocument();
    expect(within(rowFor('Status')).getByText('Published')).toHaveClass('status-indicator--success');
    expect(within(rowFor('TransXChange version')).getByText('2.4')).toBeInTheDocument();
  });

  it('links the owner to their live timetables and links the change log', () => {
    renderContent();

    expect(screen.getByRole('link', { name: 'Local Import Org' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\?organisation=5&status=live$/),
    );
    expect(screen.getByText(/Access all data uploaded by this publisher/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View change log' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/changelog\/$/),
    );
  });

  it('renders the map for the live revision and no old "Lines" / "Route map" sections', () => {
    renderContent();

    expect(screen.getByTestId('map')).toHaveAttribute('data-revision', '11');
    expect(screen.queryByRole('heading', { name: 'Lines' })).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Route map' })).not.toBeInTheDocument();
  });

  it('lists service numbers in the accordion, linking each line and service code', () => {
    renderContent();

    expect(screen.getByRole('heading', { name: 'Review Service Numbers', level: 2 })).toBeInTheDocument();
    expect(screen.getByText('PB0000001')).toBeInTheDocument();
    expect(screen.getByText('NOC1')).toBeInTheDocument();
    const link = screen.getByRole('link', { name: '14 - PB2:14' });
    expect(link.getAttribute('href')).toMatch(/\/timetable\/dataset\/1\/detail\?line=14&service=PB2%3A14$/);
    expect(screen.getAllByRole('link', { name: /^\d+ - / })).toHaveLength(3);
    expect(document.querySelector('.govuk-accordion[data-module="govuk-accordion"]')).toHaveAttribute(
      'id',
      'accordion-default',
    );
  });

  it('keeps the Review Service Numbers heading when there are no service numbers', () => {
    renderContent({ serviceNumbers: [] });

    expect(screen.getByRole('heading', { name: 'Review Service Numbers' })).toBeInTheDocument();
  });

  it('hides the API URL panel for anonymous visitors', () => {
    renderContent();

    expect(screen.queryByRole('heading', { name: 'Use this data set in your code' })).not.toBeInTheDocument();
    expect(document.getElementById('code-snippet-url')).toBeNull();
  });

  it('shows the API URL panel when signed in', () => {
    renderContent({ feedApi: 'http://data.example/api/v1/dataset/1/?api_key=abc' });

    expect(screen.getByRole('heading', { name: 'Use this data set in your code' })).toBeInTheDocument();
    expect(document.getElementById('code-snippet-url')).toHaveTextContent(
      'http://data.example/api/v1/dataset/1/?api_key=abc',
    );
  });

  it('links subscribe and download to the Django sub-pages', () => {
    renderContent();

    expect(screen.getByRole('heading', { name: 'Subscribe, download the data' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Subscribe to this data set' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/subscription\/$/),
    );
    const download = screen.getByRole('link', { name: 'Download dataset (.zip)' });
    expect(download).toHaveAttribute('href', expect.stringMatching(/\/timetable\/dataset\/1\/download\/$/));
    expect(download).not.toHaveAttribute('download');
  });

  it('offers to unsubscribe when subscribed', () => {
    renderContent({ isSubscribed: true });

    expect(screen.getByRole('link', { name: 'Unsubscribe from this data set' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Subscribe to this data set' })).not.toBeInTheDocument();
  });

  it('shows the data set feedback section when specific feedback is off', () => {
    renderContent({}, false);

    expect(screen.getByRole('heading', { name: 'Noticed issues with this data set?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact data set owner directly' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/feedback\/$/),
    );
  });

  it('hides the feedback section when specific feedback is on', () => {
    renderContent({}, true);

    expect(screen.queryByRole('heading', { name: 'Noticed issues with this data set?' })).not.toBeInTheDocument();
  });

  it('shows "Inactive" for an inactive data set', () => {
    renderContent({ status: 'inactive' });

    expect(within(rowFor('Status')).getByText('Inactive')).toHaveClass('status-indicator--inactive');
  });
});

describe('TimetableDatasetDetailContent data quality row', () => {
  const newDqs = (overrides = {}) => ({
    newDqsReport: true,
    reportId: 77,
    criticalCount: 0,
    feedbackCount: 0,
    score: null,
    cssIndicator: null,
    ragLevel: null,
    ...overrides,
  });

  it('has no row when there is no data quality information', () => {
    renderContent({ dataQuality: null });

    expect(screen.queryByRole('rowheader', { name: /Data quality report/ })).not.toBeInTheDocument();
  });

  it('shows a green NO CRITICAL ISSUES tag and the publish-host report link (new DQS)', () => {
    renderContent({ dataQuality: newDqs() });

    const row = rowFor('Data quality report');
    expect(within(row).getByText('NO CRITICAL ISSUES')).toHaveClass('govuk-tag--green');
    const link = within(row).getByRole('link', { name: 'View data quality report' });
    expect(link).toHaveAttribute('href', expect.stringMatching(/\/org\/5\/dataset\/timetable\/1\/report\/77$/));
    expect(link).toHaveAttribute('target', '_blank');
  });

  it('shows CRITICAL ISSUES when there are critical issues', () => {
    renderContent({ dataQuality: newDqs({ criticalCount: 3 }) });

    expect(within(rowFor('Data quality report')).getByText('CRITICAL ISSUES')).toHaveClass('govuk-tag--red');
  });

  it('ignores feedback counts unless specific feedback is on', () => {
    renderContent({ dataQuality: newDqs({ feedbackCount: 4 }) }, false);

    expect(within(rowFor('Data quality report')).getByText('NO CRITICAL ISSUES')).toBeInTheDocument();
  });

  it('counts feedback issues as critical when specific feedback is on', () => {
    renderContent({ dataQuality: newDqs({ feedbackCount: 4 }) }, true);

    expect(within(rowFor('Data quality report')).getByText('CRITICAL ISSUES')).toBeInTheDocument();
  });

  it('treats a missing Feedback level as non-zero when specific feedback is on', () => {
    renderContent({ dataQuality: newDqs({ feedbackCount: null }) }, true);

    expect(within(rowFor('Data quality report')).getByText('CRITICAL ISSUES')).toBeInTheDocument();
  });

  it('shows the legacy score and RAG with the report link in the third cell', () => {
    renderContent({
      dataQuality: {
        newDqsReport: false,
        reportId: 5,
        criticalCount: null,
        feedbackCount: null,
        score: '95%',
        cssIndicator: 'warning',
        ragLevel: 'AMBER',
      },
    });

    const row = rowFor('Data quality report');
    expect(within(row).getByText(/Data quality 95%/)).toBeInTheDocument();
    expect(within(row).getByText('AMBER')).toHaveClass('status-indicator--warning');
    const cells = row.querySelectorAll('td');
    expect(cells).toHaveLength(2);
    expect(within(cells[1] as HTMLElement).getByRole('link', { name: 'View data quality report' })).toBeInTheDocument();
  });

  it('opens the help modal from the help icon', () => {
    renderContent({ dataQuality: newDqs() });

    const overlay = screen.getByTestId('help-overlay');
    expect(overlay).not.toHaveClass('active');
    fireEvent.click(screen.getByRole('button', { name: 'Help: Data Quality Report' }));
    expect(overlay).toHaveClass('active');
    expect(within(overlay).getByRole('link', { name: 'found here.' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/guidance\/operator-requirements\?section=dataquality$/),
    );
    fireEvent.click(within(overlay).getByRole('button', { name: 'Close' }));
    expect(overlay).not.toHaveClass('active');
  });
});

describe('TimetableDatasetDetailContent (error panel)', () => {
  it('renders the Django error panel instead of the success content', () => {
    renderContent({ error: true, publishedBy: 'alice' });

    expect(screen.getByRole('heading', { name: 'Data set not available' })).toBeInTheDocument();
    expect(screen.getByText('22 Feb 2026 10:30 by alice')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Download previous data' })).toBeInTheDocument();
    expect(screen.getByText(/There is currently an error in this data set/)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'Would you like to provide feedback on this data set?' })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Provide feedback' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/feedback\/$/),
    );
    expect(screen.queryByTestId('map')).not.toBeInTheDocument();
    expect(screen.queryByRole('heading', { name: 'Review Service Numbers' })).not.toBeInTheDocument();
  });

  it('shows "System" when the live revision has no publisher', () => {
    renderContent({ error: true, publishedBy: null });

    expect(screen.getByText('22 Feb 2026 10:30 by System')).toBeInTheDocument();
  });

  it('links the previous data only for expired / inactive data sets', () => {
    const { unmount } = renderContent({ error: true, status: 'inactive' });
    expect(screen.getByRole('link', { name: 'Download .xml (TransXChange format)' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/timetable\/dataset\/1\/download\/$/),
    );
    unmount();

    renderContent({ error: true, status: 'live' });
    expect(screen.getByText('Download .xml (TransXChange format)')).toHaveAttribute('href', '');
  });
});

describe('shared dataset detail pieces', () => {
  it('DatasetDetailLayout renders heading, hr and the "What you need to know" sidebar', () => {
    render(
      <DatasetDetailLayout name="Heading" breadcrumbs={[{ label: 'Crumb', href: '/x' }]}>
        <p>body</p>
      </DatasetDetailLayout>,
    );

    expect(screen.getByRole('heading', { name: 'Heading', level: 1 })).toBeInTheDocument();
    expect(screen.getByText('Overview of the available bus open data')).toBeInTheDocument();
    expect(screen.getByText('body')).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: 'What you need to know' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'View developer documentation' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/guidance\/requirements$/),
    );
    expect(screen.getByRole('link', { name: 'Find out more about bus open data' })).toHaveAttribute('target', '_blank');
    expect(screen.getByRole('link', { name: 'Contact us for technical issues' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/contact$/),
    );
  });

  it.each([
    ['live', 'Published', 'status-indicator--success'],
    ['expiring', 'Soon to expire', 'status-indicator--warning'],
    ['expired', 'Expired', 'status-indicator--inactive'],
    ['error', 'Error', 'status-indicator--error'],
    ['draft', 'Draft', 'status-indicator--draft'],
    ['deleted', 'Deleted', 'status-indicator--error'],
  ])('DatasetStatusIndicator renders %s as %s', (status, text, className) => {
    render(<DatasetStatusIndicator status={status} datasetType="TIMETABLE" />);

    expect(screen.getByText(text)).toHaveClass(className);
  });

  it('DatasetStatusIndicator shows an errored AVL feed as Published', () => {
    render(<DatasetStatusIndicator status="error" datasetType="AVL" />);

    expect(screen.getByText('Published')).toHaveClass('status-indicator--success');
  });

  it('DatasetFeedbackSection uses the feed wording for AVL', () => {
    render(<DatasetFeedbackSection datasetId={3} datasetType="AVL" />);

    expect(screen.getByRole('heading', { name: 'Noticed issues with this data feed?' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact data feed owner directly' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/avl\/dataset\/3\/feedback\/$/),
    );
  });

  it('DatasetApiUrlPanel copies the URL', () => {
    const writeText = jest.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<DatasetApiUrlPanel apiUrl="http://x/y" datasetType="AVL" />);

    expect(screen.getByRole('heading', { name: 'Use this data feed in your code' })).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: 'Copy Code snippet to clipboard' }));
    expect(writeText).toHaveBeenCalledWith('http://x/y');
  });
});
