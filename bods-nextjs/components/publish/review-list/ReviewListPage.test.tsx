import { render, screen, within } from '@testing-library/react';
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

async function renderPage(kind: ReviewListKind, overrides: Partial<ReviewListResponse> = {}) {
  mockGet.mockResolvedValue(response(kind, overrides));
  render(<ReviewListPage kind={kind} />);
  return screen.findByRole('heading', { level: 1 });
}

describe('ReviewListPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = '';
    mockOrgId = '7';
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

    it('renders pagination below the table', async () => {
      await renderPage('timetable', { totalPages: 3, count: 25, hasNext: true });

      const pagination = screen.getByRole('navigation', { name: 'Pagination' });
      expect(within(pagination).getByRole('link', { name: 'Go to page 2' })).toBeInTheDocument();
      expect(within(pagination).getByRole('link', { name: 'Go to next page' })).toBeInTheDocument();
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
    it('shows the API error when the list cannot be loaded', async () => {
      mockGet.mockRejectedValue(new Error('Org user access required'));

      render(<ReviewListPage kind="timetable" />);

      expect(await screen.findByText('Org user access required')).toBeInTheDocument();
      expect(screen.queryByRole('table')).not.toBeInTheDocument();
    });
  });
});
