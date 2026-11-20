import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import AgentDashboardPage, { metadata as agentDashboardMetadata } from './page';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

let mockSearchParams = new URLSearchParams();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace: jest.fn(), refresh: jest.fn() }),
  useSearchParams: () => mockSearchParams,
  usePathname: () => '/',
}));

jest.mock('@/lib/api-client', () => ({
  api: {
    get: jest.fn(),
  },
}));

describe('Agent Dashboard - Page', () => {
  it('uses the Django page title', () => {
    expect(agentDashboardMetadata.title).toBe('Agent dashboard');
  });

  beforeEach(() => {
    jest.clearAllMocks();
    mockSearchParams = new URLSearchParams();
  });

  it('shows the empty state with a link to My Account when the user has no organisations', async () => {
    (api.get as jest.Mock).mockResolvedValue({ results: [] });

    render(<AgentDashboardPage />);

    expect(screen.getByRole('link', { name: 'Agent Dashboard' })).toHaveAttribute(
      'href',
      publishAppPath('/agent-dashboard'),
    );
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
    expect(link).toHaveAttribute('href', publishAppPath('/org/42/dataset/timetable'));
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

  describe('organisation links', () => {
    const organisation = {
      id: 42,
      name: 'Acme Buses',
      requiresAttention: 0,
      avlRequiresAttention: 0,
      faresRequiresAttention: 0,
    };

    const renderAndGetLink = async (search: string) => {
      mockSearchParams = new URLSearchParams(search);
      (api.get as jest.Mock).mockResolvedValue({ results: [organisation] });
      render(<AgentDashboardPage />);
      return screen.findByRole('link', { name: 'Acme Buses' });
    };

    it('links to the data activity page with prev when arriving from guide-me', async () => {
      const link = await renderAndGetLink('next=data-activity&prev=guide-me');
      expect(link).toHaveAttribute(
        'href',
        `${publishAppPath('/org/42/dataset/data-activity')}?prev=guide-me`,
      );
    });

    it('keeps the feed-list destination and appends prev when only prev is given', async () => {
      const link = await renderAndGetLink('prev=guide-me');
      expect(link).toHaveAttribute(
        'href',
        `${publishAppPath('/org/42/dataset/timetable')}?prev=guide-me`,
      );
    });

    it('falls back to feed-list for an unknown next value', async () => {
      const link = await renderAndGetLink('next=nonsense');
      expect(link).toHaveAttribute('href', publishAppPath('/org/42/dataset/timetable'));
    });
  });
});
