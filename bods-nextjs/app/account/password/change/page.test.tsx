import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ChangePasswordPage from './page';

const mockPush = jest.fn();
const mockRefresh = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
    refresh: mockRefresh,
  }),
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

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => ({
  getCsrfToken: () => 'csrf-token',
}));

describe('Change password page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    global.fetch = jest.fn();
  });

  it('renders the Django change-password copy and settings links', () => {
    render(<ChangePasswordPage />);

    expect(screen.getByRole('heading', { name: 'Change password' })).toBeInTheDocument();
    expect(
      screen.getByText('Your password should be at least 8 characters long.'),
    ).toBeInTheDocument();
    expect(screen.getByLabelText('Current password')).toHaveAttribute('id', 'id_oldpassword');
    expect(screen.getByLabelText('New password')).toHaveAttribute('id', 'id_password1');
    expect(screen.getByLabelText('Confirm new password')).toHaveAttribute('id', 'id_password2');
    expect(screen.getByRole('link', { name: 'Back' })).toHaveAttribute('href', '/account/settings');
    expect(screen.getByRole('link', { name: 'Cancel' })).toHaveAttribute('href', '/account/settings');
  });

  it('posts the form and goes to the done page', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: true,
      json: async () => ({}),
    });

    render(<ChangePasswordPage />);

    await userEvent.type(screen.getByLabelText('Current password'), 'oldpassword');
    await userEvent.type(screen.getByLabelText('New password'), 'newPassword_34324()()');
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newPassword_34324()()');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledWith('/api/auth/password/change/', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': 'csrf-token',
        },
        body: JSON.stringify({
          oldpassword: 'oldpassword',
          password1: 'newPassword_34324()()',
          password2: 'newPassword_34324()()',
        }),
      });
    });

    expect(mockPush).toHaveBeenCalledWith('/account/password/change/done');
  });

  it('shows field errors from the API', async () => {
    (global.fetch as jest.Mock).mockResolvedValue({
      ok: false,
      json: async () => ({
        error: 'Validation failed',
        field_errors: {
          oldpassword: ['Please type your current password.'],
        },
      }),
    });

    render(<ChangePasswordPage />);

    await userEvent.type(screen.getByLabelText('Current password'), 'wrong');
    await userEvent.type(screen.getByLabelText('New password'), 'newPassword_34324()()');
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newPassword_34324()()');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    expect(await screen.findAllByText('Please type your current password.')).not.toHaveLength(0);
    expect(mockPush).not.toHaveBeenCalled();
  });
});
