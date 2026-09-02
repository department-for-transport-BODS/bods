import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api, ApiError } from '@/lib/api-client';
import { HostProvider } from '@/lib/bods-host-context';
import PasswordResetPage from './page';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
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

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <PasswordResetPage />
    </HostProvider>,
  );
}

describe('Password reset request page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    window.sessionStorage.clear();
  });

  it('renders the Django reset-password copy', () => {
    renderPage();

    expect(screen.getByRole('heading', { name: 'Forgot your password?' })).toBeInTheDocument();
    expect(screen.getByText('Enter your email address to reset your password.')).toBeInTheDocument();
    expect(screen.getByLabelText(/Email/)).toHaveAttribute('id', 'email');
    expect(screen.getByRole('link', { name: 'Create account' })).toHaveAttribute('href', '/account/signup');
  });

  it('posts the email and goes to the done page', async () => {
    (api.post as jest.Mock).mockResolvedValue({ email: 'user@example.com' });

    renderPage();

    await userEvent.type(screen.getByLabelText(/Email/), 'user@example.com');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/password/reset/', {
        email: 'user@example.com',
      });
    });

    expect(window.sessionStorage.getItem('bods:password-reset-email')).toBe('user@example.com');
    expect(mockPush).toHaveBeenCalledWith('/account/password/reset/done');
  });

  it('shows field errors from the API against the email field', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Validation failed', 400, { email: ['Enter a valid email address.'] }),
    );

    renderPage();

    await userEvent.type(screen.getByLabelText(/Email/), 'not-an-email');
    await userEvent.click(screen.getByRole('button', { name: 'Continue' }));

    expect(await screen.findAllByText('Enter a valid email address.')).not.toHaveLength(0);
    expect(mockPush).not.toHaveBeenCalled();
  });
});
