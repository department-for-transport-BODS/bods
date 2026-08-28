import { render, screen, waitFor } from '@testing-library/react';
import { ConfirmEmailContent } from './ConfirmEmailContent';

const mockPush = jest.fn();
const mockPost = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush }),
}));

jest.mock('@/lib/api-client', () => ({
  api: { post: (...args: unknown[]) => mockPost(...args) },
}));

describe('Confirm email content', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('confirms the key from the link and offers sign in', async () => {
    mockPost.mockResolvedValue({ email: 'consumer@example.com' });

    render(<ConfirmEmailContent confirmationKey="a-valid-key" />);

    expect(screen.getByText('Confirming your email address...')).toBeInTheDocument();

    expect(await screen.findByText('Email confirmed')).toBeInTheDocument();
    expect(mockPost).toHaveBeenCalledWith('/api/auth/confirm-email/', { key: 'a-valid-key' });
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
    await waitFor(() => expect(mockPush).not.toHaveBeenCalled());
  });
});
