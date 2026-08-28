import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api } from '@/lib/api-client';
import ManageSubscriptionsPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
  },
}));

const emptyResponse = {
  muteNotifications: false,
  count: 0,
  page: 1,
  pageSize: 10,
  totalPages: 1,
  results: [],
};

const populatedResponse = {
  muteNotifications: false,
  count: 2,
  page: 1,
  pageSize: 10,
  totalPages: 1,
  results: [
    {
      id: 41,
      name: 'Timetable feed',
      datasetType: 'TIMETABLE',
      statusLabel: 'Published',
      statusClass: 'status-indicator--success',
    },
    {
      id: 77,
      name: 'AVL feed',
      datasetType: 'AVL',
      statusLabel: 'Published',
      statusClass: 'status-indicator--success',
    },
  ],
};

describe('Manage subscriptions page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the empty state when the user has no subscriptions', async () => {
    (api.get as jest.Mock).mockResolvedValue(emptyResponse);

    render(<ManageSubscriptionsPage />);

    expect(screen.getByRole('heading', { name: 'Manage subscriptions' })).toBeInTheDocument();
    await waitFor(() => {
      expect(
        screen.getByText('Your subscribed data sets will be listed here'),
      ).toBeInTheDocument();
    });
    expect(screen.queryByRole('checkbox', { name: 'Mute all subscriptions' })).not.toBeInTheDocument();
  });

  it('lists subscribed data sets with unsubscribe links', async () => {
    (api.get as jest.Mock).mockResolvedValue(populatedResponse);

    render(<ManageSubscriptionsPage />);

    await waitFor(() => {
      expect(screen.getByRole('link', { name: 'Timetable feed' })).toHaveAttribute('href', '/41');
    });
    expect(screen.getByRole('link', { name: '41' })).toHaveAttribute('href', '/41');
    expect(screen.getAllByRole('link', { name: 'Unsubscribe' })[0]).toHaveAttribute(
      'href',
      '/41/subscription',
    );
    expect(screen.getByRole('link', { name: 'AVL feed' })).toHaveAttribute('href', '/77');
    expect(screen.getAllByRole('link', { name: 'Unsubscribe' })[1]).toHaveAttribute(
      'href',
      '/77/subscription',
    );
    expect(screen.getByRole('link', { name: 'View our guidelines here' })).toHaveAttribute(
      'href',
      '/guidance/requirements',
    );
  });

  it('posts mute-all when the checkbox is toggled', async () => {
    (api.get as jest.Mock).mockResolvedValue(populatedResponse);
    (api.post as jest.Mock).mockResolvedValue({ muteNotifications: true });

    render(<ManageSubscriptionsPage />);

    const checkbox = await screen.findByRole('checkbox', { name: 'Mute all subscriptions' });
    await userEvent.click(checkbox);

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/subscriptions/mute/', {
        muteNotifications: true,
      });
    });
  });
});
