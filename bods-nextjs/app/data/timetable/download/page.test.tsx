import { render, screen, waitFor, within } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { dataPath, HOSTS } from '@/config/client';
import TimetableDownloadPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: { get: jest.fn() },
}));

const emptyData = {
  showBulkArchiveUrl: false,
  regions: [],
  changeArchives: [],
  isNewGtfsApiActive: false,
  gtfsFiles: [],
};

const populatedData = {
  showBulkArchiveUrl: true,
  regions: [
    { regionCode: 'ALL', name: 'All', exists: true },
    { regionCode: 'EA', name: 'East Anglia', exists: true },
    { regionCode: 'L', name: 'London', exists: false },
  ],
  changeArchives: [{ publishedAt: '2026-01-05', label: 'Monday 5 January' }],
  isNewGtfsApiActive: true,
  gtfsFiles: [{ id: 'south_east', name: 'South East' }],
};

describe('Timetable download page', () => {
  beforeEach(() => jest.clearAllMocks());

  it('renders the Django breadcrumbs, heading and help links', async () => {
    (api.get as jest.Mock).mockResolvedValue(emptyData);

    render(<TimetableDownloadPage />);

    const breadcrumbs = screen.getByRole('navigation', { name: 'Breadcrumb' });
    expect(
      within(breadcrumbs)
        .getAllByRole('link')
        .map((link) => [link.textContent, link.getAttribute('href')]),
    ).toEqual([
      ['Bus Open Data Service', HOSTS.www],
      ['Find Bus Open Data', HOSTS.data],
      ['Download All Data', dataPath('/downloads')],
      ['All Timetables Data', dataPath('/timetable/download/')],
    ]);
    expect(screen.getByRole('heading', { level: 1 })).toHaveTextContent('All timetables data');
    expect(screen.getByRole('link', { name: 'Service changelog' })).toBeInTheDocument();
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/api/data/browser/downloads/timetables/'));
  });

  it('shows the empty states when nothing has been published', async () => {
    (api.get as jest.Mock).mockResolvedValue(emptyData);

    render(<TimetableDownloadPage />);

    expect(
      await screen.findByText('Bulk download is not yet available. Please check back later.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('There have been no updates in the last 7 days. Please check back later.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('There are no GTFS files currently available. Please check back later.'),
    ).toBeInTheDocument();
  });

  it('links every archive to the matching file route', async () => {
    (api.get as jest.Mock).mockResolvedValue(populatedData);

    render(<TimetableDownloadPage />);

    const bulk = await screen.findByRole('link', {
      name: 'All - Download timetables data in TransXChange format',
    });
    expect(bulk).toHaveAttribute('href', dataPath('/timetable/download/bulk_archive'));
    expect(
      screen.getByRole('link', { name: 'East Anglia - Download timetables data in TransXChange format' }),
    ).toHaveAttribute('href', dataPath('/timetable/download/bulk_archive/EA'));
    // "All" is the bulk link and regions without an archive are hidden
    expect(screen.queryByText(/London - Download/)).not.toBeInTheDocument();
    expect(
      screen.getByRole('link', {
        name: 'All data set updates from Monday 5 January 00:00:00 - 23:59:59',
      }),
    ).toHaveAttribute('href', dataPath('/timetable/download/change_archive/2026-01-05/'));
    expect(
      screen.getByRole('link', { name: 'South East - Download timetables data in GTFS format' }),
    ).toHaveAttribute('href', dataPath('/timetable/download/gtfs-file/south_east/'));
    expect(screen.getByRole('link', { name: 'Traveline National Dataset (TNDS)' })).toHaveAttribute(
      'target',
      '_blank',
    );
  });

  it('shows an error when the page data cannot be loaded', async () => {
    (api.get as jest.Mock).mockRejectedValue(new Error('boom'));

    render(<TimetableDownloadPage />);

    expect(await screen.findByText('boom')).toBeInTheDocument();
  });
});
