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

  it('renders nothing visible and does not redirect while the session is being checked', () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, isLoading: true });

    const { container } = render(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );

    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
    expect(screen.queryByText('Secret')).not.toBeInTheDocument();
    expect(container).toBeEmptyDOMElement();
    expect(loginUrlWithNext).not.toHaveBeenCalled();
  });

  it('shows children once the session check resolves as signed in', () => {
    const mockedUseAuth = useAuth as jest.Mock;
    mockedUseAuth.mockReturnValue({ isAuthenticated: false, isLoading: true });

    const { rerender } = render(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );
    expect(screen.queryByText('Secret')).not.toBeInTheDocument();

    mockedUseAuth.mockReturnValue({ isAuthenticated: true, isLoading: false });
    rerender(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );

    expect(screen.getByText('Secret')).toBeInTheDocument();
    expect(loginUrlWithNext).not.toHaveBeenCalled();
  });

  it('renders nothing visible for signed-out users while redirecting', async () => {
    (useAuth as jest.Mock).mockReturnValue({ isAuthenticated: false, isLoading: false });

    const { container } = render(
      <ProtectedRoute>
        <p>Secret</p>
      </ProtectedRoute>,
    );

    expect(container).toBeEmptyDOMElement();
    await waitFor(() => expect(loginUrlWithNext).toHaveBeenCalledTimes(1));
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
