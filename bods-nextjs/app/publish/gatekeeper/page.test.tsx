import { render, screen } from '@testing-library/react';
import PublishGatekeeperPage, { metadata } from './page';
import { HOSTS, dataPath, publishPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

const setAuth = (auth: { user: { account_type: number } | null; isAuthenticated: boolean; isLoading?: boolean }) => {
  (useAuth as jest.Mock).mockReturnValue({ isLoading: false, ...auth });
};

describe('PublishGatekeeperPage', () => {
  it('uses the Django page title', () => {
    expect(metadata.title).toBe('Publish your data');
  });

  it('renders the Django heading, copy, breadcrumbs and Find open data button', () => {
    setAuth({ user: null, isAuthenticated: false });

    render(<PublishGatekeeperPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Publish your data' })).toBeInTheDocument();
    expect(
      screen.getByText('Only bus operators and local authorities are able to provide their data.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Bus Open Data Service' })).toHaveAttribute('href', HOSTS.www);
    expect(screen.getByRole('link', { name: 'Publish Open Data Service' })).toHaveAttribute('href', HOSTS.publish);
    expect(screen.getByRole('button', { name: 'Find open data' })).toHaveAttribute('href', dataPath('/'));
  });

  it('shows the login link to anonymous users without requiring sign-in', () => {
    setAuth({ user: null, isAuthenticated: false });

    render(<PublishGatekeeperPage />);

    expect(screen.getByRole('link', { name: 'Please login if you are an operator' })).toHaveAttribute(
      'href',
      publishPath('/account/login/'),
    );
  });

  it('shows nothing extra while the session is loading', () => {
    setAuth({ user: null, isAuthenticated: false, isLoading: true });

    render(<PublishGatekeeperPage />);

    expect(screen.queryByRole('link', { name: 'Please login if you are an operator' })).not.toBeInTheDocument();
  });

  it('tells developers they can access and use the data sets', () => {
    setAuth({ user: { account_type: 4 }, isAuthenticated: true });

    render(<PublishGatekeeperPage />);

    expect(screen.getByText('As a developer you can access and use these data sets.')).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Please login if you are an operator' })).not.toBeInTheDocument();
  });

  it('tells site admins they can manage organisations and accounts', () => {
    setAuth({ user: { account_type: 1 }, isAuthenticated: true });

    render(<PublishGatekeeperPage />);

    expect(screen.getByText('As a site admin you can manage organisations and accounts.')).toBeInTheDocument();
  });
});
