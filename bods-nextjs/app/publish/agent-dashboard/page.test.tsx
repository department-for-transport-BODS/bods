import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AgentDashboardPage from './page';
import { api } from '@/lib/api-client';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('Agent Dashboard - Page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the empty state with a link to My Account when the user has no organisations', async () => {
    (api.get as jest.Mock).mockResolvedValue({ results: [] });

    render(<AgentDashboardPage />);

    expect(await screen.findByText(/don't have any operators yet/)).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Go to My Account' })).toHaveAttribute(
      'href',
      '/account',
    );
  });

  it('renders organisations with requires-attention counts and links to the timetables list', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      results: [
        {
          id: 42,
          name: 'Acme Buses',
          requiresAttention: 2,
          avlRequiresAttention: 1,
          faresRequiresAttention: 0,
        },
      ],
    });

    render(<AgentDashboardPage />);

    const link = await screen.findByRole('link', { name: 'Acme Buses' });
    expect(link).toHaveAttribute('href', '/publish/org/42/dataset/timetable');
    expect(screen.getByText('2')).toBeInTheDocument();
  });

  it('searches organisations by name', async () => {
    (api.get as jest.Mock).mockResolvedValue({ results: [] });

    render(<AgentDashboardPage />);
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/api/publish/agent-dashboard/organisations/?q='));

    await userEvent.type(screen.getByPlaceholderText('Enter an operator name'), 'Acme');
    await userEvent.click(screen.getByRole('button', { name: 'submit search' }));

    await waitFor(() =>
      expect(api.get).toHaveBeenCalledWith('/api/publish/agent-dashboard/organisations/?q=Acme'),
    );
    expect(screen.getByText('Sorry, no results found for your search')).toBeInTheDocument();
  });
});
