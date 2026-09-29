import { render, screen } from '@testing-library/react';
import SelectDatasetTypePage from './page';
import { useAuth } from '@/hooks/useAuth';
import { publishAppPath } from '@/config/client';

jest.mock('next/navigation', () => ({
  useParams: () => ({ orgId: '123' }),
  useRouter: () => ({ push: jest.fn() }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

describe('Select dataset type page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows the instruction and linked current breadcrumb', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: { is_agent_user: false } });

    render(<SelectDatasetTypePage />);

    expect(screen.getByText('Please choose the type of data you would like to publish.'))
      .toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Publish a Dataset or Data Feed' }))
      .toHaveAttribute('href', publishAppPath('/org/123/dataset'));
  });

  it('includes the operator dashboard breadcrumb for agent users', () => {
    (useAuth as jest.Mock).mockReturnValue({ user: { is_agent_user: true } });

    render(<SelectDatasetTypePage />);

    expect(screen.getByRole('link', { name: 'Operator Dashboard' }))
      .toHaveAttribute('href', publishAppPath('/org'));
  });
});
