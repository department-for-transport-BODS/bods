/**
 * @jest-environment jsdom
 * @jest-environment-options {"url": "http://data.localhost:3001/api"}
 */

import { render, screen } from '@testing-library/react';
import { waitFor } from '@testing-library/dom';
import { ProtectedRoute } from './ProtectedRoute';
import { useAuth } from '@/hooks/useAuth';
import { loginUrlWithNext } from '@/lib/auth/post-login-redirect';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

// jsdom forbids real navigation, so the redirect target is asserted at this seam.
jest.mock('@/lib/auth/post-login-redirect', () => ({
  loginUrlWithNext: jest.fn(() => '#login-stub'),
}));

beforeEach(() => {
  jest.clearAllMocks();
});

describe('ProtectedRoute', () => {
  it('sends signed-out users to the login page on the host they came from', async () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, isLoading: false });

    render(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );

    await waitFor(() => expect(loginUrlWithNext).toHaveBeenCalledTimes(1));
    expect(loginUrlWithNext).toHaveBeenCalledWith(
      '/account/login',
      'http://data.localhost:3001/api',
    );
  });

  it('renders children for signed-in users', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: true, isLoading: false });

    render(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );

    expect(screen.getByText('Secret')).toBeInTheDocument();
    expect(loginUrlWithNext).not.toHaveBeenCalled();
  });
});
