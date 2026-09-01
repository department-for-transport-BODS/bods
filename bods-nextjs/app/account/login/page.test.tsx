import { render, screen, waitFor } from '@testing-library/react';
import { api } from '@/lib/api-client';
import { HostProvider } from '@/lib/bods-host-context';
import LoginPage from './page';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, refresh: jest.fn() }),
  useSearchParams: () => new URLSearchParams(),
}));

jest.mock('next/link', () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ login: jest.fn() }),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <LoginPage />
    </HostProvider>,
  );
}

describe('Login page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.get as jest.Mock).mockResolvedValue({ verifiedEmail: null });
  });

  it('shows the Django confirmed-email copy when the session has a verified address', async () => {
    (api.get as jest.Mock).mockResolvedValue({ verifiedEmail: 'consumer@example.com' });

    renderPage();

    expect(await screen.findByRole('heading', { name: 'Email address confirmed' })).toBeInTheDocument();
    expect(screen.getByText('Your email address has been confirmed.')).toBeInTheDocument();
    expect(screen.getByText('You can now sign in to your account.')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toHaveValue('consumer@example.com');
  });

  it('keeps the ordinary sign-in heading when nothing was confirmed', async () => {
    renderPage();

    expect(screen.getByRole('heading', { name: 'Sign in' })).toBeInTheDocument();
    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/api/auth/login/');
    });
    expect(screen.queryByText('Your email address has been confirmed.')).not.toBeInTheDocument();
  });
});
