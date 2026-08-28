import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { api, ApiError } from '@/lib/api-client';
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

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn(), post: jest.fn() } };
});

describe('Change password page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
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
    (api.post as jest.Mock).mockResolvedValue({});

    render(<ChangePasswordPage />);

    await userEvent.type(screen.getByLabelText('Current password'), 'oldpassword');
    await userEvent.type(screen.getByLabelText('New password'), 'newPassword_34324()()');
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newPassword_34324()()');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/api/auth/password/change/', {
        oldpassword: 'oldpassword',
        password1: 'newPassword_34324()()',
        password2: 'newPassword_34324()()',
      });
    });

    expect(mockPush).toHaveBeenCalledWith('/account/password/change/done');
  });

  it('shows field errors from the API against the right field', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Validation failed', 400, {
        oldpassword: ['Please type your current password.'],
      }),
    );

    render(<ChangePasswordPage />);

    await userEvent.type(screen.getByLabelText('Current password'), 'wrong');
    await userEvent.type(screen.getByLabelText('New password'), 'newPassword_34324()()');
    await userEvent.type(screen.getByLabelText('Confirm new password'), 'newPassword_34324()()');
    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    expect(await screen.findAllByText('Please type your current password.')).not.toHaveLength(0);
    expect(screen.getByRole('link', { name: 'Please type your current password.' })).toHaveAttribute(
      'href',
      '#id_oldpassword',
    );
    expect(mockPush).not.toHaveBeenCalled();
  });

  it('shows a non-field error from the form on the summary', async () => {
    (api.post as jest.Mock).mockRejectedValue(
      new ApiError('Validation failed', 400, { __all__: ['Please type your new password twice.'] }),
    );

    render(<ChangePasswordPage />);

    await userEvent.click(screen.getByRole('button', { name: 'Reset password' }));

    expect(await screen.findByText('Please type your new password twice.')).toBeInTheDocument();
    expect(mockPush).not.toHaveBeenCalled();
  });
});
