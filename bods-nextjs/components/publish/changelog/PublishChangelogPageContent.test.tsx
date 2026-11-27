import { render, screen } from '@testing-library/react';
import { Component, type ReactNode } from 'react';
import { publishAppPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import type { DatasetChangelog } from '@/components/data/dataset-subpages/types';
import { PublishChangelogPageContent } from './PublishChangelogPageContent';

let mockSearch = '';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '1', datasetId: '4' }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), refresh: jest.fn() }),
  usePathname: () => '/org/1/dataset/timetable/4/changelog/',
  notFound: () => {
    throw new Error('NEXT_NOT_FOUND');
  },
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

const mockGet = api.get as jest.Mock;

function changelog(overrides: Partial<DatasetChangelog> = {}): DatasetChangelog {
  return {
    datasetId: 4,
    datasetType: 'TIMETABLE',
    name: 'My timetable',
    showDataQuality: true,
    count: 2,
    page: 1,
    pageSize: 10,
    totalPages: 1,
    results: [
      {
        revisionId: 1,
        comment: 'First upload',
        statusLabel: 'Published',
        statusClass: 'status-indicator--success',
        updatedAt: '01 Jan 2024 10:00',
        showErrors: false,
        errors: [],
        dataQuality: { score: '90%', ragLevel: 'Green', indicator: 'success' },
      },
      {
        revisionId: 2,
        comment: 'Second upload',
        statusLabel: 'Error',
        statusClass: 'status-indicator--error',
        updatedAt: '02 Jan 2024 11:30',
        showErrors: true,
        errors: ['Bad file', 'Worse file'],
        dataQuality: { text: 'Not available' },
      },
    ],
    ...overrides,
  };
}

beforeEach(() => {
  jest.clearAllMocks();
  mockSearch = '';
});

describe('PublishChangelogPageContent (timetables)', () => {
  it('renders the Django table with data quality and error rows', async () => {
    mockGet.mockResolvedValue(changelog());
    render(<PublishChangelogPageContent kind="timetables" />);

    expect(await screen.findByRole('heading', { level: 1, name: 'My timetable' })).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/changelog/1/4/');
    expect(screen.getByText('Changelog', { selector: 'span.govuk-caption-xl' })).toBeInTheDocument();
    expect(screen.getAllByRole('columnheader').map((th) => th.textContent)).toEqual([
      'Comment',
      'Status',
      'Updated date',
      'Data quality',
    ]);
    expect(screen.getByText('First upload')).toBeInTheDocument();
    expect(screen.getByText('Published')).toHaveClass('status-indicator--success');
    expect(screen.getByText('02 Jan 2024 11:30')).toBeInTheDocument();
    expect(screen.getByText('Green')).toHaveClass('status-indicator--success');
    expect(screen.getByText('Not available')).toBeInTheDocument();
    expect(screen.getByText('Worse file').closest('td')).toHaveAttribute('colspan', '4');
  });

  it('links Back to the publish feed detail page with a trailing slash', async () => {
    mockGet.mockResolvedValue(changelog());
    render(<PublishChangelogPageContent kind="timetables" />);

    const back = await screen.findByRole('link', { name: 'Back' });
    expect(back).toHaveAttribute('href', publishAppPath('/org/1/dataset/timetable/4/'));
    expect(back.getAttribute('href')).not.toMatch(/\/publish\/org/);
  });

  it('passes the page query on to Django and shows table pagination', async () => {
    mockSearch = 'page=2';
    mockGet.mockResolvedValue(changelog({ page: 2, totalPages: 3 }));
    render(<PublishChangelogPageContent kind="timetables" />);

    await screen.findByRole('heading', { level: 1 });
    expect(mockGet).toHaveBeenCalledWith('/api/publish/timetables/changelog/1/4/?page=2');
    expect(screen.getByRole('link', { name: /Previous/ })).toHaveAttribute('href', expect.stringContaining('page=1'));
    expect(screen.getByRole('link', { name: /Next/ })).toHaveAttribute('href', expect.stringContaining('page=3'));
  });

  it('shows an error summary when the changelog cannot be loaded', async () => {
    mockGet.mockRejectedValue(new Error('boom'));
    render(<PublishChangelogPageContent kind="timetables" />);

    expect(await screen.findByText('Unable to load the changelog. Please refresh and try again.')).toBeInTheDocument();
  });

  it('renders the not-found page when Django answers 404', async () => {
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));
    const consoleError = jest.spyOn(console, 'error').mockImplementation(() => undefined);

    class Boundary extends Component<{ children: ReactNode }, { failed: boolean }> {
      state = { failed: false };
      static getDerivedStateFromError() {
        return { failed: true };
      }
      render() {
        return this.state.failed ? <p>not found boundary</p> : this.props.children;
      }
    }

    render(
      <Boundary>
        <PublishChangelogPageContent kind="timetables" />
      </Boundary>,
    );

    expect(await screen.findByText('not found boundary')).toBeInTheDocument();
    consoleError.mockRestore();
  });
});

describe('PublishChangelogPageContent (fares)', () => {
  it('omits the data quality column and links Back to the fares detail page', async () => {
    mockGet.mockResolvedValue(
      changelog({
        datasetType: 'FARES',
        showDataQuality: false,
        results: [
          {
            revisionId: 1,
            comment: 'Fares upload',
            statusLabel: 'Published',
            statusClass: 'status-indicator--success',
            updatedAt: '01 Jan 2024 10:00',
            showErrors: false,
            errors: [],
          },
        ],
      }),
    );
    render(<PublishChangelogPageContent kind="fares" />);

    expect(await screen.findByText('Fares upload')).toBeInTheDocument();
    expect(mockGet).toHaveBeenCalledWith('/api/publish/fares/changelog/1/4/');
    expect(screen.getAllByRole('columnheader').map((th) => th.textContent)).toEqual([
      'Comment',
      'Status',
      'Updated date',
    ]);
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute(
      'href',
      publishAppPath('/org/1/dataset/fares/4/'),
    );
  });
});
