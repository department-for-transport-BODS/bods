import { render, screen, waitFor } from '@testing-library/react';
import { ConfirmEmailContent } from './ConfirmEmailContent';

const mockReplace = jest.fn();
const mockPost = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ replace: mockReplace, push: jest.fn() }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: (...args: unknown[]) => mockPost(...args) },
}));

describe('Confirm email content', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('confirms the key from the link and goes to login', async () => {
    mockPost.mockResolvedValue({ email: 'consumer@example.com' });

    render(<ConfirmEmailContent confirmationKey="a-valid-key" />);

    expect(screen.queryByText('Confirming your email address...')).not.toBeInTheDocument();
    expect(screen.queryByText('Email confirmed')).not.toBeInTheDocument();

    await waitFor(() => {
      expect(mockPost).toHaveBeenCalledWith('/api/auth/confirm-email/', { key: 'a-valid-key' });
      expect(mockReplace).toHaveBeenCalledWith('/account/login');
    });
  });

  it('reports an invalid or expired link', async () => {
    mockPost.mockRejectedValue(new Error('This email confirmation link expired or is invalid.'));

    render(<ConfirmEmailContent confirmationKey="a-used-key" />);

    expect(
      await screen.findByText('This email confirmation link expired or is invalid.'),
    ).toBeInTheDocument();
    expect(
      screen.getByRole('link', { name: 'Issue a new email confirmation request' }),
    ).toHaveAttribute('href', '/account/login');
    await waitFor(() => expect(mockReplace).not.toHaveBeenCalled());
  });
});
