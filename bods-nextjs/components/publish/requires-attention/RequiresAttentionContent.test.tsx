import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { RequiresAttentionContent } from './RequiresAttentionContent';
import { ApiError, api } from '@/lib/api-client';

let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useRouter: () => ({ push: jest.fn() }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => '/publish/org/123/dataset/timetable/attention',
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

const populated = {
  ancestor: 'Review My Timetables Data',
  summary: { servicesRequiringAttention: 12, totalInScopeInSeasonServices: 12, percentage: 100 },
  rows: [
    { licenceNumber: 'PD1', serviceCode: 'PD1/1', lineNumber: '1A' },
    { licenceNumber: 'PD1', serviceCode: 'PD1/2', lineNumber: '2A' },
  ],
  pagination: { currentPage: 1, totalPages: 2 },
  query: '',
  noResults: false,
  exportPath: '/org/123/dataset/timetable/service-codes/',
};

describe('RequiresAttentionContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    (api.get as jest.Mock).mockResolvedValue(populated);
  });

  it('loads the timetable endpoint and renders the Django page copy, stats and table', async () => {
    render(<RequiresAttentionContent kind="timetables" />);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/publish/timetables/requires-attention/123/?q=&page=1'),
    );

    expect(
      await screen.findByRole('heading', { level: 1, name: 'Service codes requiring attention' }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/The service codes listed here are registered with the OTC and are in scope of BODS/),
    ).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
    expect(screen.getByText('Not Compliant')).toBeInTheDocument();
    expect(screen.getByText('Search for a licence number, service code or line number')).toBeInTheDocument();

    const table = screen.getByRole('table');
    expect(within(table).getAllByRole('columnheader').map((header) => header.textContent)).toEqual([
      expect.stringContaining('Licence number'),
      expect.stringContaining('Service code'),
      expect.stringContaining('Line'),
    ]);
    expect(within(table).getByText('PD1/2')).toBeInTheDocument();
  });

  it('loads the fares endpoint and uses the fares ancestor breadcrumb', async () => {
    (api.get as jest.Mock).mockResolvedValue({ ...populated, ancestor: 'Review My Fares Data' });

    render(<RequiresAttentionContent kind="fares" />);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/publish/fares/requires-attention/123/?q=&page=1'),
    );

    const ancestor = await screen.findByRole('link', { name: 'Review My Fares Data' });
    expect(ancestor.getAttribute('href')).toMatch(/\/org\/123\/dataset\/fares\/$/);
    expect(screen.getByRole('link', { name: 'Service Codes Requiring Attention' })).toBeInTheDocument();
  });

  it('breadcrumbs follow Django: BODS, Publish, list page, attention page', async () => {
    render(<RequiresAttentionContent kind="timetables" />);

    const breadcrumb = await screen.findByRole('navigation', { name: 'Breadcrumb' });
    expect(within(breadcrumb).getAllByRole('link').map((link) => link.textContent)).toEqual([
      'Bus Open Data Service',
      'Publish Bus Open Data',
      'Review My Timetables Data',
      'Service Codes Requiring Attention',
    ]);
  });

  it('links to the service-codes export returned by the API', async () => {
    render(<RequiresAttentionContent kind="timetables" />);

    const link = await screen.findByRole('link', { name: 'Download detailed export' });
    expect(link.getAttribute('href')).toMatch(/\/org\/123\/dataset\/timetable\/service-codes\/$/);
    expect(screen.getByText('Use the link below to download and view the entire list of service codes')).toBeInTheDocument();
  });

  it('links to the compliance report export when the API says so', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      ...populated,
      exportPath: '/org/123/dataset/timetable/compliance-report/',
    });

    render(<RequiresAttentionContent kind="fares" />);

    const link = await screen.findByRole('link', { name: 'Download detailed export' });
    expect(link.getAttribute('href')).toMatch(/\/org\/123\/dataset\/timetable\/compliance-report\/$/);
  });

  it('shows the Compliant tag at 0%', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      ...populated,
      summary: { servicesRequiringAttention: 0, totalInScopeInSeasonServices: 5, percentage: 0 },
      rows: [],
      noResults: true,
    });

    render(<RequiresAttentionContent kind="timetables" />);

    expect(await screen.findByText('Compliant')).toBeInTheDocument();
    expect(screen.queryByText('Not Compliant')).not.toBeInTheDocument();
  });

  it('shows the Django empty state instead of the table when there are no results', async () => {
    (api.get as jest.Mock).mockResolvedValue({ ...populated, rows: [], noResults: true });

    render(<RequiresAttentionContent kind="timetables" />);

    expect(await screen.findByRole('heading', { name: 'Sorry, no results found for your search' })).toBeInTheDocument();
    expect(screen.getByText('Having trouble finding what you want?')).toBeInTheDocument();
    expect(screen.getByText('Check your spelling and try again')).toBeInTheDocument();
    expect(screen.getByText('Use another search term')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Download detailed export' })).toBeInTheDocument();
  });

  it('passes the search query, page and sort to the API and prefills the search box', async () => {
    mockSearchParams = new URLSearchParams('q=PD1&page=2&sort=-service_code');
    (api.get as jest.Mock).mockResolvedValue({ ...populated, query: 'PD1', pagination: { currentPage: 2, totalPages: 2 } });

    render(<RequiresAttentionContent kind="timetables" />);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith(
        '/api/publish/timetables/requires-attention/123/?q=PD1&page=2&sort=-service_code',
      ),
    );
    expect(await screen.findByRole('searchbox')).toHaveValue('PD1');
  });

  it('renders sortable headers that follow the django-tables2 sort cycle', async () => {
    mockSearchParams = new URLSearchParams('q=PD1&sort=service_code');

    render(<RequiresAttentionContent kind="timetables" />);

    const licence = await screen.findByRole('button', { name: /Licence number/ });
    expect(licence.getAttribute('href')).toBe('?q=PD1&sort=licence_number&page=1');

    const serviceCode = screen.getByRole('button', { name: /Service code/ });
    expect(serviceCode.getAttribute('href')).toBe('?q=PD1&sort=-service_code&page=1');
    expect(serviceCode.closest('th')).toHaveAttribute('aria-sort', 'ascending');
    expect(licence.closest('th')).toHaveAttribute('aria-sort', 'none');
  });

  it('opens the Line help modal', async () => {
    render(<RequiresAttentionContent kind="timetables" />);

    const help = await screen.findByRole('button', { name: 'Help' });
    const overlay = help.nextElementSibling as HTMLElement;
    expect(overlay).not.toHaveClass('active');

    await userEvent.click(help);
    await waitFor(() => expect(overlay).toHaveClass('active'));
    expect(within(overlay).getByRole('heading', { name: 'Line' })).toBeInTheDocument();
    expect(within(overlay).getByText(/data from the OTC database/)).toBeInTheDocument();
  });

  it('shows pagination when there is more than one page', async () => {
    render(<RequiresAttentionContent kind="timetables" />);

    expect(await screen.findByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
  });

  it('shows an error when the API fails', async () => {
    (api.get as jest.Mock).mockRejectedValue(new ApiError('Organisation access required', 403, {}));

    render(<RequiresAttentionContent kind="timetables" />);

    expect(await screen.findByText('Organisation access required')).toBeInTheDocument();
    expect(screen.queryByRole('table')).not.toBeInTheDocument();
  });
});
