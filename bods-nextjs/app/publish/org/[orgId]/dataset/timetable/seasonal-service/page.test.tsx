import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SeasonalServicesPage from './page';
import { api } from '@/lib/api-client';

const mockReplace = jest.fn();
let mockSearch = '';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '55' }),
  usePathname: () => '/org/55/dataset/timetable/seasonal-service',
  useRouter: () => ({ push: jest.fn(), replace: mockReplace }),
  useSearchParams: () => new URLSearchParams(mockSearch),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  ...jest.requireActual('@/lib/api-client'),
  api: { get: jest.fn(), post: jest.fn() },
}));

const row = (id: number, code: number) => ({
  id,
  licenceNumber: 'ZZ0000001',
  registrationCode: code,
  serviceCode: `ZZ0000001/${code}`,
  start: '2026-11-12',
  end: '2027-02-10',
  serviceBegins: '12/11/2026',
  serviceEnds: '10/02/2027',
});

const listResponse = (overrides: Record<string, unknown> = {}) => ({
  organisationId: 55,
  organisationName: 'ZZ Org',
  isAgentUser: false,
  counter: 2,
  results: [row(1, 100), row(2, 101)],
  sort: 'service_ends',
  pagination: { page: 1, totalPages: 1, count: 2, pageSize: 10 },
  ...overrides,
});

describe('Seasonal services - list page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = '';
    (api.get as jest.Mock).mockResolvedValue(listResponse());
  });

  it('renders the Django breadcrumbs, masthead, counter and table columns', async () => {
    render(<SeasonalServicesPage />);

    expect(await screen.findByRole('heading', { level: 1, name: 'Seasonal service operating dates' })).toBeInTheDocument();
    const crumbs = screen.getByRole('navigation', { name: /breadcrumb/i });
    expect(within(crumbs).getByRole('link', { name: 'Bus Open Data Service' })).toBeInTheDocument();
    expect(within(crumbs).getByRole('link', { name: 'Publish Open Data Service' })).toBeInTheDocument();
    expect(within(crumbs).getByRole('link', { name: 'Review My Timetables Data' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/55/dataset/timetable/'),
    );
    expect(within(crumbs).getByRole('link', { name: 'Manage seasonal services' })).toBeInTheDocument();
    expect(screen.getByText('Seasonal services')).toBeInTheDocument();
    expect(screen.getByText('2')).toHaveClass('review-stat__top');

    for (const label of ['Licence number', 'Service code', 'Service begins', 'Service ends']) {
      expect(screen.getByRole('button', { name: new RegExp(`^${label}`) })).toBeInTheDocument();
    }
    expect(screen.getByRole('columnheader', { name: 'Actions' })).toBeInTheDocument();
    expect(screen.getByText('ZZ0000001/100')).toBeInTheDocument();
  });

  it('links the default sort column to a descending sort and the others to ascending', async () => {
    render(<SeasonalServicesPage />);

    await screen.findByText('ZZ0000001/100');
    expect(screen.getByRole('button', { name: /^Service ends/ })).toHaveAttribute('href', '?sort=-service_ends&page=1');
    expect(screen.getByRole('button', { name: /^Licence number/ })).toHaveAttribute('href', '?sort=licence_number&page=1');
    expect(screen.getByRole('columnheader', { name: /^Service ends/ })).toHaveAttribute('aria-sort', 'ascending');
  });

  it('requests the page and sort from the URL', async () => {
    mockSearch = 'sort=-service_begins&page=2';
    render(<SeasonalServicesPage />);

    await screen.findByText('ZZ0000001/100');
    expect(api.get).toHaveBeenCalledWith('/api/publish/seasonal-services/55/?sort=-service_begins&page=2');
  });

  it('renders the empty state', async () => {
    (api.get as jest.Mock).mockResolvedValue(listResponse({ counter: 0, results: [] }));
    render(<SeasonalServicesPage />);

    expect(await screen.findByText('No seasonal services added.')).toBeInTheDocument();
    expect(screen.getByText("Click 'Add new date range' to add a service.")).toBeInTheDocument();
  });

  it('links to edit dates and add new keeping the page', async () => {
    (api.get as jest.Mock).mockResolvedValue(
      listResponse({ pagination: { page: 2, totalPages: 3, count: 22, pageSize: 10 } }),
    );
    render(<SeasonalServicesPage />);

    const edit = (await screen.findAllByRole('link', { name: 'Edit dates' }))[0];
    expect(edit).toHaveAttribute('href', expect.stringContaining('/org/55/dataset/timetable/seasonal-service/1/edit-date?page=2&'));
    expect(screen.getByRole('button', { name: 'Add new date range' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/55/dataset/timetable/seasonal-service/add-new?page=2&'),
    );
    expect(screen.getByRole('button', { name: 'Close' })).toHaveAttribute(
      'href',
      expect.stringContaining('/org/55/dataset/timetable'),
    );
  });

  it('deletes a row through the API and reloads the list on the returned page', async () => {
    (api.post as jest.Mock).mockResolvedValue({ deleted: true, page: 1 });
    render(<SeasonalServicesPage />);

    await screen.findByText('ZZ0000001/100');
    (api.get as jest.Mock).mockResolvedValue(listResponse({ counter: 1, results: [row(2, 101)] }));
    await userEvent.click(screen.getAllByRole('button', { name: 'Delete' })[0]);

    await waitFor(() =>
      expect(api.post).toHaveBeenCalledWith('/api/publish/seasonal-services/55/delete/', { id: 1, page: '1' }),
    );
    await waitFor(() => expect(screen.queryByText('ZZ0000001/100')).not.toBeInTheDocument());
    expect(mockReplace).toHaveBeenCalledWith('/org/55/dataset/timetable/seasonal-service?page=1');
  });

  it('shows an error when the list cannot be loaded', async () => {
    (api.get as jest.Mock).mockRejectedValue(new Error('Boom'));
    render(<SeasonalServicesPage />);

    expect(await screen.findByText('Boom')).toBeInTheDocument();
  });
});
