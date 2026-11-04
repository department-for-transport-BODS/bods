import { render, screen, waitFor, within } from '@testing-library/react';
import { ApiError, api } from '@/lib/api-client';
import { TimetableFeedDetailContent } from './TimetableFeedDetailContent';
import type { TimetableFeedDetail } from './timetableFeedDetailTypes';

const mockNotFound = jest.fn();
const accordionInit = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '9' }),
  useRouter: () => ({ push: jest.fn() }),
  notFound: () => mockNotFound(),
}));

jest.mock('govuk-frontend', () => ({
  Accordion: class {
    constructor(root: HTMLElement) {
      accordionInit(root);
    }
  },
}));

jest.mock('@/components/data/MapboxRouteMap', () => ({
  MapboxRouteMap: ({ revisionId, ariaLabel }: { revisionId: number; ariaLabel: string }) => (
    <div data-testid="map" data-revision={revisionId} aria-label={ariaLabel} />
  ),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

const mockGet = api.get as jest.Mock;

const feed: TimetableFeedDetail = {
  orgId: 1,
  datasetId: 9,
  liveRevisionId: 42,
  name: 'A very long publisher feed name',
  description: 'Feed description',
  shortDescription: 'Short desc',
  ownerName: 'Test Org',
  urlLink: null,
  transxchangeVersion: '2.4',
  status: 'success',
  datasetStatus: 'live',
  publishedAt: '2026-04-10T14:20:00+00:00',
  publishedAtDisplay: '10 Apr 2026 14:20',
  publishedBy: 'publisher',
  severeErrors: [],
  dataQuality: { reportId: null, isNewService: false, hasCriticalIssues: null, rag: null },
  showPti: true,
  hasPtiViolations: false,
  distinctAttributes: { PD0001: { NOC1: { '42': ['PB0000001:1'], '7': ['PB0000001:2'] } } },
};

function renderPage(overrides: Partial<TimetableFeedDetail> = {}) {
  mockGet.mockResolvedValue({ ...feed, ...overrides });
  return render(<TimetableFeedDetailContent />);
}

function row(name: string) {
  return screen.getByRole('rowheader', { name }).closest('tr') as HTMLElement;
}

describe('TimetableFeedDetailContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('loads the feed detail and renders the heading, breadcrumbs and help links', async () => {
    renderPage();

    expect(await screen.findByRole('heading', { name: feed.name, level: 1 })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/feed-detail/1/9/');
    expect(document.title).toBe('Data set details');
    expect(screen.getByText('Preview your service data status and make changes')).toBeInTheDocument();

    const breadcrumbs = within(screen.getByRole('navigation', { name: 'Breadcrumb' }));
    expect(breadcrumbs.getByRole('link', { name: 'Bus Open Data Service' })).toBeInTheDocument();
    expect(breadcrumbs.getByRole('link', { name: 'Publish Bus Open Data' })).toBeInTheDocument();
    expect(breadcrumbs.getByRole('link', { name: 'Choose data type' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/org\/1\/dataset$/),
    );
    expect(breadcrumbs.getByRole('link', { name: 'Timetables Data Sets' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/org\/1\/dataset\/timetable$/),
    );
    expect(breadcrumbs.getByRole('link', { name: 'A very long publish...' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/org\/1\/dataset\/timetable\/9$/),
    );

    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      expect.stringContaining('/guidance/operator-requirements'),
    );
    expect(screen.getByRole('link', { name: 'Contact support desk' })).toHaveAttribute(
      'href',
      expect.stringContaining('/contact'),
    );
  });

  it('renders the map for the live revision and the property table rows in Django order', async () => {
    renderPage();

    expect(await screen.findByTestId('map')).toHaveAttribute('data-revision', '42');
    const headers = screen.getAllByRole('rowheader').map((header) => header.textContent?.trim());
    expect(headers).toEqual([
      'Name',
      'Data set ID',
      'URL link',
      'Description',
      'Short description',
      'Status',
      'Data quality report',
      'TransXChange Validation Report',
      'Owner',
      'TransXChange version',
      'Download TransXChange',
      'Last updated',
    ]);
    expect(within(row('Data set ID')).getByText('9')).toBeInTheDocument();
    expect(within(row('Owner')).getByText('Test Org')).toBeInTheDocument();
    expect(within(row('TransXChange version')).getByText('2.4')).toBeInTheDocument();
    expect(within(row('Last updated')).getByText('10 Apr 2026 14:20 by publisher')).toBeInTheDocument();
    expect(within(row('Last updated')).getByRole('link', { name: 'View change log' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/1/dataset/timetable/9/changelog'),
    );
  });

  it('links description edits and the publisher / download links to the Django routes', async () => {
    renderPage();
    await screen.findByRole('heading', { level: 1 });

    const edits = screen.getAllByRole('link', { name: 'Edit' });
    expect(edits).toHaveLength(2);
    edits.forEach((link) => expect(link).toHaveAttribute('href', expect.stringContaining('/org/1/dataset/timetable/9/dataset-edit')));
    expect(screen.getByRole('link', { name: 'Publisher URL' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/1/dataset/timetable/9/download?is_review=false'),
    );
    expect(screen.getByRole('link', { name: 'Download .xml (TxC)' })).toHaveAttribute(
      'href',
      expect.stringMatching(/\/org\/1\/dataset\/timetable\/9\/download$/),
    );
  });

  it('uses the publisher URL for both links when the feed has one', async () => {
    renderPage({ urlLink: 'https://example.com/feed.xml' });
    await screen.findByRole('heading', { level: 1 });

    expect(screen.getByRole('link', { name: 'Publisher URL' })).toHaveAttribute('href', 'https://example.com/feed.xml');
    expect(screen.getByRole('link', { name: 'Download .xml (TxC)' })).toHaveAttribute(
      'href',
      'https://example.com/feed.xml',
    );
  });

  it('shows the status with a developer-view link, and System when nobody published it', async () => {
    renderPage({ publishedBy: null });
    await screen.findByRole('heading', { level: 1 });

    const status = row('Status');
    expect(within(status).getByText('Published')).toHaveClass('status-indicator--success');
    expect(within(status).getByRole('link', { name: 'Preview developer view' })).toHaveAttribute(
      'href',
      expect.stringContaining('/timetable/dataset/9'),
    );
    expect(within(row('Last updated')).getByText('10 Apr 2026 14:20 by System')).toBeInTheDocument();
  });

  describe('data quality row', () => {
    it('shows "Generating..." while there is no report', async () => {
      renderPage();
      await screen.findByRole('heading', { level: 1 });

      expect(within(row('Data quality report')).getByText('Generating...')).toBeInTheDocument();
      expect(within(row('Data quality report')).queryByRole('link')).not.toBeInTheDocument();
    });

    it('shows the legacy score and RAG level with report links', async () => {
      renderPage({
        dataQuality: {
          reportId: 5,
          isNewService: false,
          hasCriticalIssues: null,
          rag: { score: '91%', ragLevel: 'amber', cssIndicator: 'warning' },
        },
      });
      await screen.findByRole('heading', { level: 1 });

      const cell = within(row('Data quality report'));
      expect(cell.getByText('AMBER')).toHaveClass('status-indicator--warning');
      expect(cell.getByText(/91%/)).toBeInTheDocument();
      const view = cell.getByRole('link', { name: 'View data quality report' });
      expect(view).toHaveAttribute('href', expect.stringContaining('/org/1/dataset/timetable/9/report/5'));
      expect(view).toHaveAttribute('target', '_blank');
      expect(view).toHaveAttribute('rel', 'noopener noreferrer');
      expect(cell.getByRole('link', { name: 'Download data quality report.csv' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/report/5/csv'),
      );
      expect(cell.queryByText('Generating...')).not.toBeInTheDocument();
    });

    it('shows the new data quality service tags', async () => {
      const { unmount } = renderPage({
        dataQuality: { reportId: 5, isNewService: true, hasCriticalIssues: false, rag: null },
      });
      expect(await within(await screenRow('Data quality report')).findByText('NO CRITICAL ISSUES')).toHaveClass(
        'govuk-tag--green',
      );
      unmount();

      renderPage({ dataQuality: { reportId: 5, isNewService: true, hasCriticalIssues: true, rag: null } });
      expect(await within(await screenRow('Data quality report')).findByText('CRITICAL ISSUES')).toHaveClass(
        'govuk-tag--red',
      );
    });
  });

  describe('TransXChange validation row', () => {
    it('reports a pass', async () => {
      renderPage();
      await screen.findByRole('heading', { level: 1 });

      const cell = within(row('TransXChange Validation Report'));
      expect(cell.getByText('Successfully passed validation')).toBeInTheDocument();
      expect(cell.getByText('Your data is BODS compliant.')).toBeInTheDocument();
    });

    it('reports violations with a download link', async () => {
      renderPage({ hasPtiViolations: true });
      await screen.findByRole('heading', { level: 1 });

      const cell = within(row('TransXChange Validation Report'));
      expect(cell.getByText('3a Validation check – Passed with issues')).toBeInTheDocument();
      expect(cell.getByRole('link', { name: 'Download validation report' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/violations-csv'),
      );
      expect(cell.getByText(/Some of the files in the data supplied is non-compliant/)).toBeInTheDocument();
    });

    it('is hidden when PTI does not apply to the revision', async () => {
      renderPage({ showPti: false });
      await screen.findByRole('heading', { level: 1 });

      expect(screen.queryByRole('rowheader', { name: 'TransXChange Validation Report' })).not.toBeInTheDocument();
    });
  });

  describe('service numbers accordion', () => {
    it('lists line and service code links under licence and NOC, and initialises the accordion', async () => {
      renderPage();

      expect(await screen.findByRole('heading', { name: 'Review Service Numbers' })).toBeInTheDocument();
      expect(screen.getByText('PD0001')).toBeInTheDocument();
      expect(screen.getByText('NOC1')).toBeInTheDocument();
      expect(screen.getByRole('link', { name: '42 - PB0000001:1' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/detail?line=42&service=PB0000001%3A1'),
      );
      expect(screen.getByRole('link', { name: '7 - PB0000001:2' })).toBeInTheDocument();
      await waitFor(() => expect(accordionInit).toHaveBeenCalled());
    });

    it('renders an empty accordion when there are no services', async () => {
      renderPage({ distinctAttributes: {} });

      expect(await screen.findByRole('heading', { name: 'Review Service Numbers' })).toBeInTheDocument();
      expect(screen.queryByText('PD0001')).not.toBeInTheDocument();
    });
  });

  describe('actions', () => {
    it('offers update and deactivate for a live data set', async () => {
      renderPage();
      await screen.findByRole('heading', { level: 1 });

      expect(screen.getByRole('button', { name: 'Update data set' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/update'),
      );
      expect(screen.getByRole('button', { name: 'Deactivate data set' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/deactivate'),
      );
    });

    it('hides deactivate when expired', async () => {
      renderPage({ datasetStatus: 'expired' });
      await screen.findByRole('heading', { level: 1 });

      expect(screen.getByRole('button', { name: 'Update data set' })).toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Deactivate data set' })).not.toBeInTheDocument();
      expect(within(row('Status')).getByText('Expired')).toBeInTheDocument();
    });

    it('hides both when inactive', async () => {
      renderPage({ datasetStatus: 'inactive' });
      await screen.findByRole('heading', { level: 1 });

      expect(screen.queryByRole('button', { name: 'Update data set' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Deactivate data set' })).not.toBeInTheDocument();
      expect(within(row('Status')).getByText('Inactive')).toBeInTheDocument();
    });
  });

  describe('error status', () => {
    const errored: Partial<TimetableFeedDetail> = {
      status: 'error',
      datasetStatus: 'error',
      severeErrors: ['Bad file one', 'Bad file two'],
    };

    it('shows the error panel with the severe errors and recovery actions', async () => {
      renderPage(errored);

      expect(await screen.findByRole('heading', { name: 'Data set not available' })).toBeInTheDocument();
      expect(screen.getByRole('heading', { name: 'There is a problem' })).toBeInTheDocument();
      expect(screen.getByText('Bad file one')).toHaveClass('app-error-summary__item');
      expect(screen.getByText('Bad file two')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Publish correct data set' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/update'),
      );
      expect(screen.getByRole('heading', { name: 'What should I do next?' })).toBeInTheDocument();
      expect(screen.getByText(/You can re-upload a different data feed file again/)).toBeInTheDocument();
      expect(
        screen.getByText('You can delete this data set to stop using https://www.arriva.co.uk/timetables'),
      ).toBeInTheDocument();
      expect(screen.getByText('Accepted file formats include .xml (TransXChange).')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Delete data' })).toHaveAttribute(
        'href',
        expect.stringContaining('/org/1/dataset/timetable/9/delete'),
      );
    });

    it('shows only name, owner and last updated, without the map or success content', async () => {
      renderPage(errored);
      await screen.findByRole('heading', { name: 'Data set not available' });

      expect(screen.getAllByRole('rowheader').map((header) => header.textContent?.trim())).toEqual([
        'Name',
        'Owner',
        'Last updated',
      ]);
      expect(screen.queryByTestId('map')).not.toBeInTheDocument();
      expect(screen.queryByRole('heading', { name: 'Review Service Numbers' })).not.toBeInTheDocument();
      expect(screen.queryByRole('button', { name: 'Update data set' })).not.toBeInTheDocument();
      expect(screen.getByRole('link', { name: 'Contact support desk' })).toBeInTheDocument();
    });
  });

  it('calls notFound when the API returns 404', async () => {
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));
    render(<TimetableFeedDetailContent />);

    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error summary for other failures', async () => {
    mockGet.mockRejectedValue(new ApiError('Forbidden', 403, {}));
    render(<TimetableFeedDetailContent />);

    expect(
      await screen.findByText('Unable to load the data set details. Please refresh and try again.'),
    ).toBeInTheDocument();
  });
});

async function screenRow(name: string) {
  const header = await screen.findByRole('rowheader', { name });
  return header.closest('tr') as HTMLElement;
}
