import { act, render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ReviewListPage } from './ReviewListPage';
import { api } from '@/lib/api-client';
import type {
  AvlBanner,
  FaresBanner,
  ReviewListColumn,
  ReviewListKind,
  ReviewListResponse,
  ReviewListRow,
  TimetableBanner,
} from './types';

const mockPush = jest.fn();
let mockSearch = '';
let mockOrgId = '7';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: mockOrgId }),
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  usePathname: () => `/org/${mockOrgId}/dataset/timetable`,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

jest.mock('@/components/publish/AvlMatchingHelpModal', () => ({
  AvlMatchingHelpModal: () => <span data-testid="matching-help" />,
}));

const mockGet = api.get as jest.Mock;

const col = (
  key: string,
  label: string,
  extra: Partial<ReviewListColumn> = {},
): ReviewListColumn => ({
  key,
  label,
  orderable: true,
  nextSort: key,
  direction: null,
  width: null,
  ...extra,
});

const COLUMNS: Record<ReviewListKind, ReviewListColumn[]> = {
  timetable: [
    col('status', 'Status'),
    col('name', 'Data set name', { width: '25%' }),
    col('id', 'Data set ID', { direction: 'asc', nextSort: '-id' }),
    col('modified', 'Last updated'),
    col('short_description', 'Short description', { width: '20%' }),
  ],
  avl: [
    col('status', 'Status'),
    col('percent_matching', 'AVL to Timetable matching'),
    col('name', 'Data feed name', { width: '25%' }),
    col('id', 'Data feed ID', { direction: 'asc', nextSort: '-id' }),
    col('avl_feed_last_checked', 'Last automated update'),
    col('short_description', 'Short description'),
  ],
  fares: [
    col('status', 'Status'),
    col('name', 'Data set name', { width: '20%' }),
    col('id', 'Data set ID', { direction: 'asc', nextSort: '-id' }),
    col('modified', 'Last updated', { width: '25%' }),
    col('short_description', 'Short description', { width: '20%' }),
  ],
};

const TITLES: Record<ReviewListKind, string> = {
  timetable: 'timetables',
  avl: 'bus location',
  fares: 'fares',
};

const row = (overrides: Partial<ReviewListRow> = {}): ReviewListRow => ({
  id: 11,
  name: 'First feed',
  shortDescription: 'A description',
  status: 'live',
  datasetType: 1,
  hasDraftRevision: false,
  draftStatus: null,
  link: '/org/7/dataset/timetable/11/',
  modified: '2026-04-10T13:20:47Z',
  modifiedDisplay: 'April 10, 2026, 2:20 p.m.',
  ...overrides,
});

const TIMETABLE_BANNER: TimetableBanner = {
  servicesRequiringAttention: 3,
  applicableServices: 40,
  feedbackCount: 12,
  seasonalServicesCounter: 2,
};

const AVL_BANNER: AvlBanner = {
  totalConsumerInteractions: 9,
  overallPpcScore: 87,
  isAvlRequireAttentionActive: true,
  servicesRequiringAttention: 4,
  applicableServices: 50,
};

const FARES_BANNER: FaresBanner = {
  totalConsumerInteractions: 15,
  isFaresRequireAttentionActive: false,
  servicesRequiringAttention: 1,
  applicableServices: 8,
};

function response(
  kind: ReviewListKind,
  overrides: Partial<ReviewListResponse> = {},
): ReviewListResponse {
  const banners = { timetable: TIMETABLE_BANNER, avl: AVL_BANNER, fares: FARES_BANNER };
  return {
    tab: 'active',
    pageTitle: `Review my ${TITLES[kind]} data`,
    organisation: { id: 7, name: 'Acme Buses' },
    isAgentUser: false,
    sort: '',
    columns: COLUMNS[kind],
    page: 1,
    pageSize: 10,
    totalPages: 1,
    count: 1,
    hasNext: false,
    hasPrevious: false,
    banner: banners[kind],
    results: [row()],
    ...overrides,
  };
}

const PROGRESS_URL = /^\/api\/publish\/dataset\/(\d+)\/progress\/$/;
let progressResponder: (datasetId: string) => Promise<unknown> = async () => ({
  progress: 0,
  status: 'indexing',
});

function mockApi(list: ReviewListResponse) {
  mockGet.mockImplementation((url: string) => {
    const progress = PROGRESS_URL.exec(url);
    return progress ? progressResponder(progress[1]) : Promise.resolve(list);
  });
}

async function renderPage(kind: ReviewListKind, overrides: Partial<ReviewListResponse> = {}) {
  mockApi(response(kind, overrides));
  render(<ReviewListPage kind={kind} />);
  return screen.findByRole('heading', { level: 1 });
}

describe('ReviewListPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = '';
    mockOrgId = '7';
    progressResponder = async () => ({ progress: 0, status: 'indexing' });
  });

  describe('data fetching (filters, sorting and paging)', () => {
    it.each([
      ['timetable', '/api/publish/timetables/list/7/'],
      ['avl', '/api/publish/avl/list/7/'],
      ['fares', '/api/publish/fares/list/7/'],
    ] as const)('loads the %s list endpoint', async (kind, url) => {
      await renderPage(kind);

      expect(mockGet).toHaveBeenCalledWith(url);
    });

    it.each(['timetable', 'avl', 'fares'] as const)(
      'forwards tab, sort and page query params for %s',
      async (kind) => {
        mockSearch = 'tab=draft&sort=-name&page=2&unrelated=x';

        await renderPage(kind, { tab: 'draft' });

        const url = mockGet.mock.calls[0][0] as string;
        const [path, query] = url.split('?');
        expect(path).toMatch(new RegExp(`/list/7/$`));
        expect(Object.fromEntries(new URLSearchParams(query))).toEqual({
          tab: 'draft',
          sort: '-name',
          page: '2',
        });
      },
    );
  });

  describe('masthead and breadcrumbs', () => {
    it('sets the browser title from Django, including the agent organisation name', async () => {
      await renderPage('timetable', {
        isAgentUser: true,
        pageTitle: 'Review Acme Buses timetables data',
      });

      expect(document.title).toBe('Review Acme Buses timetables data');
    });

    it.each(['timetable', 'avl', 'fares'] as const)(
      'shows the Django title for an org user on %s',
      async (kind) => {
        const heading = await renderPage(kind);

        expect(heading).toHaveTextContent(`Review my ${TITLES[kind]} data`);
        expect(screen.queryByRole('link', { name: 'Agent Dashboard' })).not.toBeInTheDocument();
        const crumbs = screen.getByRole('navigation', { name: 'Breadcrumb' });
        // Django links the last crumb to the timetable feed-list on all three pages.
        expect(
          within(crumbs).getByRole('link', {
            name: `Review My ${TITLES[kind].replace(/\b\w/g, (c) => c.toUpperCase())} Data`,
          }),
        ).toHaveAttribute('href', expect.stringMatching(/\/org\/7\/dataset\/timetable$/));
      },
    );

    it('uses the organisation name and an Agent Dashboard crumb for agents', async () => {
      const heading = await renderPage('timetable', {
        isAgentUser: true,
        pageTitle: "Review O'neil Coaches timetables data",
      });

      expect(heading).toHaveTextContent("Review O'neil Coaches timetables data");
      expect(screen.getByRole('link', { name: 'Agent Dashboard' })).toBeInTheDocument();
      expect(screen.getByText("Review O'Neil Coaches Timetables Data")).toBeInTheDocument();
    });
  });

  describe('blue banner', () => {
    it('shows the three timetable stats with Django links', async () => {
      await renderPage('timetable');
      const banner = document.querySelector('.review-banner') as HTMLElement;

      expect(within(banner).getAllByText(/Total service codes|Feedback messages|Seasonal/)).toHaveLength(3);
      expect(banner.querySelectorAll('.review-stat')).toHaveLength(3);
      expect(within(banner).getByText('3')).toBeInTheDocument();
      expect(within(banner).getByText('/40')).toBeInTheDocument();
      expect(within(banner).getByText('12')).toBeInTheDocument();
      expect(within(banner).getByText('2')).toBeInTheDocument();
      const hrefs = within(banner)
        .getAllByRole('link')
        .map((link) => link.getAttribute('href') ?? '');
      expect(hrefs[0]).toMatch(/\/org\/7\/dataset\/timetable\/attention$/);
      expect(hrefs[1]).toMatch(/\/org\/7\/dataset\/data-activity\?prev=feed-list$/);
      expect(hrefs[2]).toMatch(/\/org\/7\/dataset\/timetable\/seasonal-service$/);
      expect(within(banner).getByRole('link', { name: 'Manage' })).toBeInTheDocument();
    });

    it('shows consumer interactions, matching score and attention for AVL', async () => {
      await renderPage('avl');
      const banner = document.querySelector('.review-banner') as HTMLElement;

      expect(banner.querySelectorAll('.review-stat')).toHaveLength(3);
      expect(within(banner).getByText('Total consumer interactions with your data')).toBeInTheDocument();
      expect(within(banner).getByText(/87%/)).toBeInTheDocument();
      expect(within(banner).getByRole('link', { name: 'Download all archived matching reports' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/ppc-archive$/),
      );
      expect(within(banner).getByText('/50')).toBeInTheDocument();
      expect(within(banner).getAllByTestId('matching-help')).toHaveLength(1);
    });

    it('shows Pending and no archive link when there is no AVL score', async () => {
      await renderPage('avl', {
        banner: { ...AVL_BANNER, overallPpcScore: null, isAvlRequireAttentionActive: false },
      });
      const banner = document.querySelector('.review-banner') as HTMLElement;

      expect(within(banner).getByText(/Pending/)).toBeInTheDocument();
      expect(within(banner).queryByRole('link', { name: /archived matching reports/ })).not.toBeInTheDocument();
      expect(banner.querySelectorAll('.review-stat')).toHaveLength(2);
    });

    it('shows a score of 0% rather than Pending', async () => {
      await renderPage('avl', { banner: { ...AVL_BANNER, overallPpcScore: 0 } });

      expect(screen.getByText(/^0%/)).toBeInTheDocument();
      expect(screen.queryByText(/Pending/)).not.toBeInTheDocument();
    });

    it('shows the fares attention stat when the flag is on', async () => {
      await renderPage('fares', {
        banner: { ...FARES_BANNER, isFaresRequireAttentionActive: true },
      });
      const banner = document.querySelector('.review-banner') as HTMLElement;

      expect(banner.querySelectorAll('.review-stat')).toHaveLength(1);
      expect(within(banner).getByText('Total service codes that require attention')).toBeInTheDocument();
      expect(within(banner).getByText('/8')).toBeInTheDocument();
      expect(within(banner).getByRole('link', { name: 'More details' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/fares\/attention$/),
      );
    });

    it('shows consumer interactions for fares when the flag is off', async () => {
      await renderPage('fares');
      const banner = document.querySelector('.review-banner') as HTMLElement;

      expect(within(banner).getByText('15')).toBeInTheDocument();
      expect(within(banner).getByRole('link', { name: 'More details' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/data-activity\?prev=fares-feed-list$/),
      );
    });
  });

  describe('data type selector and tabs', () => {
    it.each([
      ['timetable', 'Timetables data'],
      ['avl', 'Bus location data'],
      ['fares', 'Fares data'],
    ] as const)('selects the current type on %s', async (kind, label) => {
      await renderPage(kind);

      const select = screen.getByLabelText('Select data type') as HTMLSelectElement;
      expect(select.selectedOptions[0]).toHaveTextContent(label);
    });

    it('navigates to the chosen data type', async () => {
      await renderPage('timetable');

      await userEvent.selectOptions(screen.getByLabelText('Select data type'), 'Fares data');

      expect(mockPush).toHaveBeenCalledWith(expect.stringMatching(/\/org\/7\/dataset\/fares$/));
    });

    it('links the three tabs and marks the active one selected', async () => {
      await renderPage('timetable', { tab: 'draft' });

      const tabs = screen.getAllByRole('link', { name: /^(Active|Draft|Inactive)$/ });
      expect(tabs.map((tab) => tab.getAttribute('href'))).toEqual([
        '?tab=active',
        '?tab=draft',
        '?tab=archive',
      ]);
      expect(screen.getByRole('link', { name: 'Draft' }).closest('li')).toHaveClass(
        'govuk-tabs__list-item--selected',
      );
      expect(screen.getByRole('link', { name: 'Active' }).closest('li')).not.toHaveClass(
        'govuk-tabs__list-item--selected',
      );
    });

    it('moves focus to the selected tab once loaded, like Django', async () => {
      await renderPage('timetable', { tab: 'archive' });

      expect(screen.getByRole('link', { name: 'Inactive' })).toHaveFocus();
    });
  });

  describe('table', () => {
    it.each([
      ['timetable', ['Status', 'Data set name', 'Data set ID', 'Last updated', 'Short description']],
      [
        'avl',
        [
          'Status',
          'AVL to Timetable matching',
          'Data feed name',
          'Data feed ID',
          'Last automated update',
          'Short description',
        ],
      ],
      ['fares', ['Status', 'Data set name', 'Data set ID', 'Last updated', 'Short description']],
    ] as const)('renders the %s columns', async (kind, labels) => {
      await renderPage(kind);

      const headers = screen.getAllByRole('columnheader');
      expect(headers.map((header) => header.textContent?.replace(/Sort your data by .*/, '').trim())).toEqual(
        labels,
      );
    });

    it('applies column widths as Django does', async () => {
      await renderPage('timetable');

      const headers = screen.getAllByRole('columnheader');
      expect(headers[1]).toHaveAttribute('width', '25%');
      expect(headers[4]).toHaveAttribute('width', '20%');
      expect(headers[0]).not.toHaveAttribute('width');
    });

    it('builds sort links that keep the query and reset the page', async () => {
      mockSearch = 'tab=draft&page=3';
      await renderPage('timetable', { tab: 'draft', page: 3, totalPages: 4 });

      const sortLink = screen.getByRole('button', { name: /Data set name/ });
      const params = new URLSearchParams((sortLink.getAttribute('href') ?? '').replace(/^\?/, ''));
      expect(Object.fromEntries(params)).toEqual({ tab: 'draft', sort: 'name', page: '1' });
    });

    it('marks the sorted column with aria-sort and a direction class', async () => {
      await renderPage('timetable', {
        sort: '-id',
        columns: [
          col('status', 'Status'),
          col('id', 'Data set ID', { direction: 'desc', nextSort: 'id' }),
        ],
      });

      const [status, id] = screen.getAllByRole('columnheader');
      expect(status).toHaveAttribute('aria-sort', 'none');
      expect(id).toHaveAttribute('aria-sort', 'descending');
      expect(id).toHaveClass('desc');
      expect(within(id).getByRole('button')).toHaveAttribute(
        'href',
        expect.stringContaining('sort=id'),
      );
    });

    it('renders Django cell values and the row link', async () => {
      await renderPage('timetable');

      const cells = within(screen.getAllByRole('row')[1]).getAllByRole('cell');
      expect(cells[0]).toHaveTextContent('Published');
      expect(within(cells[1]).getByRole('link', { name: 'First feed' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/timetable\/11$/),
      );
      expect(cells[2]).toHaveTextContent('11');
      expect(cells[3]).toHaveTextContent('April 10, 2026, 2:20 p.m.');
      expect(cells[4]).toHaveTextContent('A description');
    });

    it('leaves the name unlinked when Django gives no link', async () => {
      await renderPage('timetable', { results: [row({ link: null })] });

      expect(screen.queryByRole('link', { name: 'First feed' })).not.toBeInTheDocument();
      expect(screen.getByText('First feed')).toBeInTheDocument();
    });

    it('renders AVL matching and last automated update values', async () => {
      await renderPage('avl', {
        results: [
          row({
            datasetType: 2,
            link: '/org/7/dataset/avl/11/',
            percentMatching: '87%',
            avlFeedLastCheckedDisplay: 'April 12, 2026, 9:01 a.m.',
          }),
        ],
      });

      const cells = within(screen.getAllByRole('row')[1]).getAllByRole('cell');
      expect(cells[1]).toHaveTextContent('87%');
      expect(cells[4]).toHaveTextContent('April 12, 2026, 9:01 a.m.');
    });

    it('shows a message instead of a table when there are no data sets', async () => {
      await renderPage('fares', { results: [], count: 0 });

      expect(screen.getByText('No data sets found')).toBeInTheDocument();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });

    it('renders Django table pagination below the table', async () => {
      await renderPage('timetable', { totalPages: 3, count: 25, hasNext: true });

      const pagination = screen.getByRole('navigation', { name: 'Pagination' });
      expect(pagination.querySelectorAll('li a')).toHaveLength(3);
      expect(pagination).toHaveTextContent('Next');
      expect(pagination.querySelector('a[rel="next"]')).toHaveAttribute('href', '?page=2');
    });

    it('keeps the tab and sort in pagination links, as Django does', async () => {
      mockSearch = 'tab=draft&sort=-name&page=2';

      await renderPage('timetable', { tab: 'draft', page: 2, totalPages: 3 });

      const pagination = screen.getByRole('navigation', { name: 'Pagination' });
      expect(pagination.querySelector('a[rel="prev"]')).toHaveAttribute(
        'href',
        '?page=1&tab=draft&sort=-name',
      );
      expect(pagination.querySelector('a[rel="next"]')).toHaveAttribute(
        'href',
        '?page=3&tab=draft&sort=-name',
      );
    });
  });

  describe('status column', () => {
    const statusText = async (kind: ReviewListKind, overrides: Partial<ReviewListRow>) => {
      await renderPage(kind, { results: [row(overrides)] });
      return within(screen.getAllByRole('row')[1]).getAllByRole('cell')[0];
    };

    it('shows a published live dataset with a draft and its view links', async () => {
      const cell = await statusText('timetable', {
        hasDraftRevision: true,
        draftStatus: 'success',
      });

      expect(cell).toHaveTextContent('Published');
      expect(cell).toHaveTextContent('Draft');
      const hrefs = within(cell)
        .getAllByRole('link', { name: 'View' })
        .map((link) => link.getAttribute('href') ?? '');
      expect(hrefs[0]).toMatch(/\/org\/7\/dataset\/timetable\/11$/);
      expect(hrefs[1]).toMatch(/\/org\/7\/dataset\/timetable\/11\/update\/review$/);
    });

    it('uses avl paths for AVL view links', async () => {
      const cell = await statusText('avl', {
        datasetType: 2,
        hasDraftRevision: true,
        draftStatus: 'success',
      });

      expect(within(cell).getAllByRole('link', { name: 'View' })[0]).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/avl\/11$/),
      );
    });

    it('shows Processing without a second view link while a draft is indexing', async () => {
      const cell = await statusText('timetable', {
        hasDraftRevision: true,
        draftStatus: 'indexing',
      });

      expect(cell).toHaveTextContent('Processing');
      expect(within(cell).getAllByRole('link', { name: 'View' })).toHaveLength(1);
    });

    it('shows Error for a failed draft', async () => {
      const cell = await statusText('timetable', {
        hasDraftRevision: true,
        draftStatus: 'error',
      });

      expect(cell).toHaveTextContent('Error');
    });

    it.each([
      ['indexing', 'Processing'],
      ['pending', 'Processing'],
      ['warning', 'Warning'],
      ['expiring', 'Soon to expire'],
      ['error', 'Error'],
      ['draft', 'Draft'],
      ['success', 'Draft'],
      ['expired', 'Expired'],
      ['inactive', 'Inactive'],
      ['deleted', 'Deleted'],
    ])('maps %s to "%s"', async (status, label) => {
      const cell = await statusText('timetable', { status });

      expect(cell).toHaveTextContent(label);
    });

    it('shows an errored AVL feed as Published', async () => {
      const cell = await statusText('avl', { status: 'error', datasetType: 2 });

      expect(cell).toHaveTextContent('Published');
    });
  });

  describe('processing progress polling (feed-list-progress.js)', () => {
    const progressCalls = () =>
      mockGet.mock.calls.filter(([url]) => PROGRESS_URL.test(url as string));

    const renderProcessing = async (overrides: Partial<ReviewListRow> = { status: 'indexing' }) => {
      mockApi(response('timetable', { results: [row(overrides)] }));
      render(<ReviewListPage kind="timetable" />);
      await screen.findByRole('table');
      await act(async () => {
        await jest.advanceTimersByTimeAsync(0);
      });
    };

    const tick = (ms: number) =>
      act(async () => {
        await jest.advanceTimersByTimeAsync(ms);
      });

    const cell = () => within(screen.getAllByRole('row')[1]).getAllByRole('cell')[0];

    beforeEach(() => {
      jest.useFakeTimers();
    });

    afterEach(() => {
      jest.useRealTimers();
    });

    it('queries the dataset progress endpoint straight away and then every 10 seconds', async () => {
      await renderProcessing();

      expect(progressCalls()).toEqual([['/api/publish/dataset/11/progress/']]);

      await tick(9999);
      expect(progressCalls()).toHaveLength(1);
      await tick(1);
      expect(progressCalls()).toHaveLength(2);
      await tick(10000);
      expect(progressCalls()).toHaveLength(3);
    });

    it('updates the pie arc and percentage while the revision is indexing', async () => {
      progressResponder = async () => ({ progress: 40, status: 'indexing' });
      await renderProcessing();

      expect(cell()).toHaveTextContent('40%');
      expect(cell()).toHaveTextContent('Processing');
      const arc = cell().querySelector('path')?.getAttribute('d') ?? '';
      expect(arc).toMatch(/^M [\d.-]+ [\d.-]+ A 4\.5 4\.5 0 0 0 [\d.-]+ [\d.-]+$/);

      progressResponder = async () => ({ progress: 80, status: 'indexing' });
      await tick(10000);

      expect(cell()).toHaveTextContent('80%');
      // 81% of a circle is more than half, so the large-arc flag is set.
      expect(cell().querySelector('path')?.getAttribute('d')).toContain('A 4.5 4.5 0 1 0');
      expect(progressCalls()).toHaveLength(2);
    });

    it('swaps to Draft with a View link on the active tab and stops polling', async () => {
      progressResponder = async () => ({ progress: 100, status: 'success' });
      await renderProcessing();

      expect(cell().querySelector('.status-indicator--draft')).toHaveTextContent('Draft');
      expect(cell().querySelector('.pie-progress')).toBeNull();
      expect(within(cell()).getByRole('link', { name: 'View' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/org\/7\/dataset\/timetable\/11\/update\/review$/),
      );

      await tick(60000);
      expect(progressCalls()).toHaveLength(1);
    });

    it('swaps to Error and stops polling', async () => {
      progressResponder = async () => ({ progress: 100, status: 'error' });
      await renderProcessing();

      expect(cell().querySelector('.status-indicator--error')).toHaveTextContent('Error');
      await tick(30000);
      expect(progressCalls()).toHaveLength(1);
    });

    it.each([
      ['pending', 30],
      ['live', 100],
      ['indexing', 100],
    ])('falls back to the success-styled "Processing" for %s at %i%% and stops', async (status, progress) => {
      progressResponder = async () => ({ progress, status });
      await renderProcessing();

      expect(cell().querySelector('.status-indicator--success')).toHaveTextContent('Processing');
      await tick(30000);
      expect(progressCalls()).toHaveLength(1);
    });

    it('gives up and shows the fallback indicator when the request fails', async () => {
      const consoleError = jest.spyOn(console, 'error').mockImplementation(() => {});
      progressResponder = async () => {
        throw new Error('503');
      };
      await renderProcessing();

      expect(cell().querySelector('.status-indicator--success')).toHaveTextContent('Processing');
      expect(consoleError).toHaveBeenCalledWith(expect.stringContaining('Cannot contact API, giving up'));
      await tick(30000);
      expect(progressCalls()).toHaveLength(1);
      consoleError.mockRestore();
    });

    it('does not add the View link on the draft tab', async () => {
      mockSearch = 'tab=draft';
      progressResponder = async () => ({ progress: 100, status: 'success' });
      await renderProcessing();

      expect(cell()).toHaveTextContent('Draft');
      expect(within(cell()).queryByRole('link', { name: 'View' })).not.toBeInTheDocument();
    });

    it('polls the draft revision of a published dataset and keeps its Published badge', async () => {
      progressResponder = async () => ({ progress: 100, status: 'success' });
      await renderProcessing({ status: 'live', hasDraftRevision: true, draftStatus: 'indexing' });

      expect(cell()).toHaveTextContent('Published');
      expect(cell().querySelector('.status-indicator--draft')).toHaveTextContent('Draft');
      expect(within(cell()).getAllByRole('link', { name: 'View' })).toHaveLength(2);
      expect(progressCalls()).toEqual([['/api/publish/dataset/11/progress/']]);
    });

    it('does not poll rows that are not processing', async () => {
      await renderProcessing({ status: 'draft' });
      await tick(30000);

      expect(progressCalls()).toHaveLength(0);
    });

    it('polls each processing row independently', async () => {
      mockApi(
        response('timetable', {
          results: [row({ id: 11, status: 'indexing' }), row({ id: 12, status: 'pending' })],
        }),
      );
      progressResponder = async (id) =>
        id === '11' ? { progress: 100, status: 'success' } : { progress: 25, status: 'indexing' };
      render(<ReviewListPage kind="timetable" />);
      await screen.findByRole('table');
      await tick(0);

      const rows = screen.getAllByRole('row');
      expect(rows[1]).toHaveTextContent('Draft');
      expect(rows[2]).toHaveTextContent('25%');
      await tick(10000);
      expect(progressCalls().filter(([url]) => url === '/api/publish/dataset/11/progress/')).toHaveLength(1);
      expect(progressCalls().filter(([url]) => url === '/api/publish/dataset/12/progress/')).toHaveLength(2);
    });

    it('stops polling when the page is left', async () => {
      mockApi(response('timetable', { results: [row({ status: 'indexing' })] }));
      const { unmount } = render(<ReviewListPage kind="timetable" />);
      await screen.findByRole('table');
      await tick(0);
      unmount();

      await tick(30000);
      expect(progressCalls()).toHaveLength(1);
    });
  });

  describe('footer', () => {
    it.each([
      ['timetable', 'Publish new data sets', /\/org\/7\/dataset\/timetable\/new$/],
      ['avl', 'Publish new data feeds', /\/org\/7\/dataset\/avl\/new$/],
      ['fares', 'Publish new data sets', /\/org\/7\/dataset\/fares\/new$/],
    ] as const)('links the %s publish button', async (kind, label, href) => {
      await renderPage(kind);

      expect(screen.getByRole('button', { name: label })).toHaveAttribute(
        'href',
        expect.stringMatching(href),
      );
    });

    it('links the guidance and licence setup help', async () => {
      await renderPage('timetable');

      expect(screen.getByRole('link', { name: 'Bus operator requirements' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/guidance\/operator-requirements$/),
      );
      expect(screen.getByRole('link', { name: 'Local authority requirements' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/guidance\/local-authority-requirements$/),
      );
      expect(screen.getByRole('link', { name: 'Set up licence numbers' })).toHaveAttribute(
        'href',
        expect.stringMatching(/\/account\/manage\/org-profile\/7$/),
      );
    });
  });

  describe('errors', () => {
    const rejectWithStatus = (message: string, status: number) =>
      mockGet.mockRejectedValue(Object.assign(new Error(message), { status }));

    it('shows the API error when the list cannot be loaded', async () => {
      rejectWithStatus('Boom', 500);

      render(<ReviewListPage kind="timetable" />);

      expect(await screen.findByText('Boom')).toBeInTheDocument();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
      expect(
        screen.queryByRole('heading', { name: /you don’t have permissions/ }),
      ).not.toBeInTheDocument();
    });

    // OrgUserViewMixin: abods users, non-org users and users from another organisation all get
    // Django's 403 page, never the list.
    it.each(['timetable', 'avl', 'fares'] as const)(
      'shows Django’s 403 page on %s when the API refuses the user',
      async (kind) => {
        rejectWithStatus('Org user access required', 403);

        render(<ReviewListPage kind={kind} />);

        expect(
          await screen.findByRole('heading', {
            level: 1,
            name: 'We are sorry but you don’t have permissions to access this.',
          }),
        ).toBeInTheDocument();
        expect(
          screen.getByText("Please liase with your organisation's admin for further information."),
        ).toBeInTheDocument();
        expect(screen.queryByText('Org user access required')).not.toBeInTheDocument();
        expect(screen.queryByRole('table')).not.toBeInTheDocument();
        expect(screen.queryByText('Contact support')).not.toBeInTheDocument();
        expect(document.title).toBe('Forbidden (403)');
      },
    );
  });
});
