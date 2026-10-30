import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { LocalAuthorityListContent } from '@/components/data/local-authority/LocalAuthorityListContent';
import { ApiError, api } from '@/lib/api-client';

const mockPush = jest.fn();
const mockNotFound = jest.fn();
let mockSearch = '';

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
  usePathname: () => '/local-authority',
  useSearchParams: () => new URLSearchParams(mockSearch),
  notFound: () => mockNotFound(),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

const mockGet = api.get as jest.Mock;

const listResponse = (overrides = {}) => ({
  q: '',
  ordering: 'ui_lta_name_trimmed',
  count: 12,
  page: 1,
  numPages: 2,
  pageSize: 10,
  pageRange: [1, 2],
  names: ['Bournemouth', 'Kent'],
  results: [
    { name: 'Bournemouth Council', authIds: [1, 2], servicesRequireAttentionPercentage: 42 },
    { name: 'Kent County Council', authIds: [3], servicesRequireAttentionPercentage: 0 },
  ],
  ...overrides,
});

describe('LocalAuthorityListContent', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearch = '';
  });

  it('renders the masthead, breadcrumbs, result count and rows like Django', async () => {
    mockGet.mockResolvedValue(listResponse());

    render(<LocalAuthorityListContent />);

    expect(await screen.findByText('12 results')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Local Transport Authority' })).toBeInTheDocument();
    expect(screen.getByText('Search for a specific Local Transport Authority')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter Local Transport Authority name')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Local Transport Authority Profiles' })).toBeInTheDocument();
    expect(screen.getAllByText('Services requiring attention:')).toHaveLength(2);
    expect(screen.getByText('42 %')).toBeInTheDocument();

    const link = screen.getByRole('link', { name: 'Bournemouth Council' });
    const href = link.getAttribute('href') ?? '';
    expect(href).toContain('/local-authority/detail?auth_ids=');
    expect(decodeURIComponent(href.split('auth_ids=')[1])).toBe('[1, 2]');
    expect(screen.getByRole('option', { name: 'Name A-Z' })).toBeInTheDocument();
    expect(screen.getByRole('option', { name: 'Name Z-A' })).toBeInTheDocument();
    expect(screen.getByRole('navigation', { name: 'Pagination' })).toBeInTheDocument();
  });

  it('requests the list API with q, ordering and page from the URL', async () => {
    mockSearch = 'q=kent&ordering=-ui_lta_name_trimmed&page=2';
    mockGet.mockResolvedValue(listResponse({ q: 'kent', ordering: '-ui_lta_name_trimmed', page: 2 }));

    render(<LocalAuthorityListContent />);

    await waitFor(() => expect(mockGet).toHaveBeenCalled());
    const url = mockGet.mock.calls[0][0] as string;
    expect(url).toContain('/browser/local-authority/?');
    expect(url).toContain('q=kent');
    expect(url).toContain('ordering=-ui_lta_name_trimmed');
    expect(url).toContain('page=2');
    expect(await screen.findByText('Containing')).toBeInTheDocument();
  });

  it('shows the singular count and the empty state', async () => {
    mockGet.mockResolvedValueOnce(
      listResponse({ count: 1, results: [listResponse().results[0]], numPages: 1, pageRange: [1] }),
    );
    const { unmount } = render(<LocalAuthorityListContent />);
    expect(await screen.findByText('1 result')).toBeInTheDocument();
    unmount();

    mockSearch = 'q=zzz';
    mockGet.mockResolvedValueOnce(listResponse({ q: 'zzz', count: 0, results: [], pageRange: [] }));
    render(<LocalAuthorityListContent />);

    expect(await screen.findByRole('heading', { name: 'Sorry, no results found for zzz' })).toBeInTheDocument();
    expect(screen.getByText('Having trouble finding what you want?')).toBeInTheDocument();
    expect(screen.getByText('Check your spelling and try again')).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: 'Pagination' })).not.toBeInTheDocument();
  });

  it('submits a search and a sort change back to page 1', async () => {
    mockSearch = 'page=2';
    mockGet.mockResolvedValue(listResponse({ page: 2 }));
    const user = userEvent.setup();

    render(<LocalAuthorityListContent />);
    await screen.findByText('12 results');

    await user.selectOptions(screen.getByLabelText('Sort by'), '-ui_lta_name_trimmed');
    expect(mockPush).toHaveBeenLastCalledWith('/local-authority?ordering=-ui_lta_name_trimmed');

    await user.type(screen.getByPlaceholderText('Enter Local Transport Authority name'), 'kent{Enter}');
    expect(mockPush).toHaveBeenLastCalledWith('/local-authority?q=kent&ordering=ui_lta_name_trimmed');
  });

  it('renders the Next.js 404 when Django returns 404 for the page', async () => {
    mockSearch = 'page=99';
    mockGet.mockRejectedValue(new ApiError('Not found', 404, {}));

    render(<LocalAuthorityListContent />);

    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error for other failures', async () => {
    mockGet.mockRejectedValue(new ApiError('boom', 500, {}));

    render(<LocalAuthorityListContent />);

    expect(await screen.findByText('Failed to load local transport authorities')).toBeInTheDocument();
  });
});
