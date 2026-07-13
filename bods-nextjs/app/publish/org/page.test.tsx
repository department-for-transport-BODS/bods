import { render, screen } from '@testing-library/react';
import { waitFor } from '@testing-library/dom';
import SelectOrgPage from './page';
import { getPaginated } from '@/lib/api-client';
import { useAuth } from '@/hooks/useAuth';

const mockPush = jest.fn();

jest.mock('next/navigation', () => ({
  useRouter: () => ({
    push: mockPush,
  }),
  useSearchParams: () => new URLSearchParams('dataType=timetable'),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

jest.mock('@/lib/api-client', () => ({
  getPaginated: jest.fn(),
}));

describe('SelectOrgPage routing', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('keeps non-single organisation users on organisation selection', async () => {
    (useAuth as jest.Mock).mockReturnValue({
      user: {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: false,
        organisation_id: 123,
      },
    });
    (getPaginated as jest.Mock).mockResolvedValue({
      results: [{ id: 123, name: 'OrganisationOne' }],
    });

    render(<SelectOrgPage />);

    await waitFor(() => expect(screen.getByText('OrganisationOne')).toBeInTheDocument());
    expect(mockPush).not.toHaveBeenCalled();
  });
});