import { render, waitFor } from '@testing-library/react';
import LogoutPage from './page';

const mockPush = jest.fn();
const mockRefresh = jest.fn();
const mockSignOut = jest.fn().mockResolvedValue(undefined);

jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: mockPush, refresh: mockRefresh }),
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({
    signOut: mockSignOut,
    isAuthenticated: true,
    isLoading: false,
  }),
}));

describe('Logout page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockSignOut.mockResolvedValue(undefined);
  });

  it('signs the user out then goes to the Django logout-success URL', async () => {
    render(<LogoutPage />);

    await waitFor(() => {
      expect(mockSignOut).toHaveBeenCalled();
      expect(mockPush).toHaveBeenCalledWith('/account/logout-success');
    });
  });
});
