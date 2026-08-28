import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TimetableReviewPage from './page';
import { api } from '@/lib/api-client';

const mockPush = jest.fn();
let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useRouter: () => ({ push: mockPush }),
  useSearchParams: () => mockSearchParams,
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('Timetable - Review - Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
    (api.get as jest.Mock).mockResolvedValue({ tab: 'active', results: [] });
  });

  it('loads the active tab by default and links to the create wizard', async () => {
    render(<TimetableReviewPage />);

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/publish/timetables/list/123/?tab=active'),
    );

    expect(screen.getByRole('link', { name: 'Publish new data feeds' })).toHaveAttribute(
      'href',
      '/publish/org/123/dataset/timetable/new',
    );
  });

  it('renders draft datasets with a link to their review page', async () => {
    mockSearchParams = new URLSearchParams('tab=draft');
    (api.get as jest.Mock).mockResolvedValue({
      tab: 'draft',
      results: [{ id: 456, name: 'My timetable', status: 'draft', modified: '2024-01-01T00:00:00Z' }],
    });

    render(<TimetableReviewPage />);

    const link = await screen.findByRole('link', { name: 'My timetable' });
    expect(link).toHaveAttribute('href', '/publish/org/123/dataset/timetable/456/review');
  });

  it('renders active datasets as text only, since there is no detail page yet', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      tab: 'active',
      results: [{ id: 789, name: 'Live timetable', status: 'live', modified: '2024-01-01T00:00:00Z' }],
    });

    render(<TimetableReviewPage />);

    await screen.findByText('Live timetable');
    expect(screen.queryByRole('link', { name: 'Live timetable' })).not.toBeInTheDocument();
  });

  it('navigates to the selected dataset type page', async () => {
    render(<TimetableReviewPage />);
    await waitFor(() => expect(api.get).toHaveBeenCalled());

    await userEvent.selectOptions(screen.getByLabelText('Select data type'), '/publish/org/123/dataset/avl');

    expect(mockPush).toHaveBeenCalledWith('/publish/org/123/dataset/avl');
  });
});
