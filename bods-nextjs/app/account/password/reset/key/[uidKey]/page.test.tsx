import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api, ApiError } from '@/lib/api-client';
import { HostProvider } from '@/lib/bods-host-context';
import PasswordResetFromKeyPage from './page';

const mockGoToSuccess = jest.fn();

jest.mock('next/navigation', () => ({
  useParams: () => ({ uidKey: 'MQ-abc-def' }),
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

jest.mock('@/lib/auth/password-reset', () => {
  const actual = jest.requireActual('@/lib/auth/password-reset');
  return { ...actual, goToPasswordResetSuccess: (...args: unknown[]) => mockGoToSuccess(...args) };
});

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <PasswordResetFromKeyPage />
    </HostProvider>,
  );
}

describe('Password reset from key page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the new-password form when the link is valid', async () => {
    (api.get as jest.Mock).mockResolvedValue({ valid: true });

    renderPage();

    expect(await screen.findByText('Enter your new password in the field below.')).toBeInTheDocument();
    expect(screen.getByLabelText('New password')).toHaveAttribute('id', 'id_password1');
    expect(screen.getByLabelText('Confirm new password')).toHaveAttribute('id', 'id_password2');
    expect(api.get).toHaveBeenCalledWith(
      '/api/auth/password/reset/key/?uidb36=MQ&key=abc-def',
    );
  });

  it('shows the invalid-link copy when the key is rejected', async () => {
    (api.get as jest.Mock).mockRejectedValue(new ApiError('Invalid', 400, {}));

    renderPage();

    expect(await screen.findByText('The link you have used is invalid')).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'new password reset' })).toHaveAttribute(
      'href',
      '/account/password/reset',
    );
  });

  it('posts the new password and goes to the done page', async () => {
    (api.get as jest.Mock).mockResolvedValue({ valid: true });
    (api.post as jest.Mock).mockResolvedValue({ user: { id: 1 } });

    renderPage();

    await screen.findByLabelText('New password');
    await userEvent.type(screen.getByLabelText('New password'), 'newPassword_34324()()');
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newPassword_34324()()');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/password/reset/key/', {
        uidb36: 'MQ',
        key: 'abc-def',
        password1: 'newPassword_34324()()',
        password2: 'newPassword_34324()()',
      });
    });

    expect(mockGoToSuccess).toHaveBeenCalled();
  });
});
