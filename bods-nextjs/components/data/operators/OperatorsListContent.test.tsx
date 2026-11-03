import { render, screen, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { OperatorsListContent } from './OperatorsListContent';
import { ApiError, api } from '@/lib/api-client';
import { dataPath } from '@/config/client';
import type { OperatorListResponse } from '@/lib/operators';

const mockPush = jest.fn();
const mockNotFound = jest.fn();
let mockSearch = '';

jest.mock('next/navigation', () => ({
  usePathname: () => '/operators',
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => new URLSearchParams(mockSearch),
  notFound: () => mockNotFound(),
}));

jest.mock('@/lib/api-client', () => {
  class MockApiError extends Error {
    status: number;
    constructor(message: string, status: number) {
      super(message);
      this.status = status;
    }
  }
  return { api: { get: jest.fn() }, ApiError: MockApiError };
});

function response(overrides: Partial<OperatorListResponse> = {}): OperatorListResponse {
  return {
    q: '',
    ordering: 'name',
    count: 2,
    page: 1,
    numPages: 1,
    pageSize: 10,
    pageRange: [1],
    results: [
      { id: 7, name: 'Alpha Buses Ltd', created: '2023-03-05T10:00:00Z' },
      { id: 9, name: 'Beta Coaches', created: '2024-11-30T10:00:00Z' },
    ],
    operatorNames: ['Alpha Buses Ltd', 'Beta Coaches'],
    ...overrides,
  };
}

describe('OperatorsListContent', () => {
  beforeEach(() => {
    mockSearch = '';
    jest.mocked(api.get).mockResolvedValue(response());
  });
  afterEach(() => jest.clearAllMocks());

  it('renders the Django banner, count, results and registration dates', async () => {
    render(<OperatorsListContent />);

    expect(await screen.findByText('2 results')).toBeInTheDocument();
    expect(screen.getByRole('heading', { level: 1, name: 'Operator Profiles' })).toBeInTheDocument();
    expect(screen.getByText('Search for a specific operator')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter operator name')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Alpha Buses Ltd' })).toHaveAttribute(
      'href',
      dataPath('/operators/7/'),
    );
    expect(screen.getAllByText('Date registered:')).toHaveLength(2);
    expect(screen.getByText('5 March 2023')).toBeInTheDocument();
    expect(screen.getByText('30 November 2024')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Operator Profiles' }).closest('li')).toHaveAttribute(
      'aria-current',
      'page',
    );
  });

  it('shows "1 result" for a single match', async () => {
    jest.mocked(api.get).mockResolvedValue(
      response({ count: 1, results: [{ id: 7, name: 'Alpha Buses Ltd', created: '2023-03-05T10:00:00Z' }] }),
    );
    render(<OperatorsListContent />);
    expect(await screen.findByText('1 result')).toBeInTheDocument();
  });

  it('shows the empty state with the search term', async () => {
    mockSearch = 'q=zzz';
    jest.mocked(api.get).mockResolvedValue(response({ q: 'zzz', count: 0, results: [], pageRange: [] }));
    render(<OperatorsListContent />);

    expect(await screen.findByText('Sorry, no results found for zzz')).toBeInTheDocument();
    expect(screen.getByText('Having trouble finding what you want?')).toBeInTheDocument();
    expect(screen.getByText('Check your spelling and try again')).toBeInTheDocument();
    expect(screen.getByText('Containing')).toBeInTheDocument();
    expect(screen.queryByRole('navigation', { name: /pagination/i })).not.toBeInTheDocument();
  });

  it('passes the query, ordering and page to the API', async () => {
    mockSearch = 'q=alp&ordering=-created&page=2';
    render(<OperatorsListContent />);

    await screen.findByText('2 results');
    expect(api.get).toHaveBeenCalledWith('/api/data/browser/operators/?q=alp&ordering=-created&page=2');
  });

  it('offers the four Django sort options and navigates on change', async () => {
    render(<OperatorsListContent />);
    await screen.findByText('2 results');

    const sort = screen.getByLabelText('Sort by');
    expect(within(sort).getAllByRole('option').map((option) => option.textContent)).toEqual([
      'Name A-Z',
      'Name Z-A',
      'Date registered newest',
      'Date registered oldest',
    ]);

    await userEvent.selectOptions(sort, '-created');
    expect(mockPush).toHaveBeenCalledWith('/operators?ordering=-created');
  });

  it('submits a search back to page 1', async () => {
    mockSearch = 'ordering=-name&page=3';
    render(<OperatorsListContent />);
    await screen.findByText('2 results');

    await userEvent.type(screen.getByPlaceholderText('Enter operator name'), 'be{enter}');
    expect(mockPush).toHaveBeenCalledWith('/operators?q=be&ordering=-name');
  });

  it('suggests operator names from the second typed character', async () => {
    render(<OperatorsListContent />);
    await screen.findByText('2 results');

    await userEvent.type(screen.getByPlaceholderText('Enter operator name'), 'al');
    expect(await screen.findByText('Alpha Buses Ltd', { selector: 'strong' })).toBeInTheDocument();
  });

  it('builds pagination links with the page first, then the other params', async () => {
    mockSearch = 'q=a&ordering=name&page=2';
    jest.mocked(api.get).mockResolvedValue(
      response({ q: 'a', count: 30, page: 2, numPages: 3, pageRange: [1, 2, 3] }),
    );
    render(<OperatorsListContent />);
    await screen.findByText('30 results');

    expect(screen.getByRole('link', { name: 'Page 3' })).toHaveAttribute(
      'href',
      '/operators?page=3&q=a&ordering=name',
    );
  });

  it('calls notFound() when the page is out of range', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('Invalid page', 404, {}));
    render(<OperatorsListContent />);
    await waitFor(() => expect(mockNotFound).toHaveBeenCalled());
  });

  it('shows an error when the API fails', async () => {
    jest.mocked(api.get).mockRejectedValue(new ApiError('boom', 500, {}));
    render(<OperatorsListContent />);
    expect(await screen.findByText('Failed to load operators')).toBeInTheDocument();
  });
});
