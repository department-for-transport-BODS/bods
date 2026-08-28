import { render, screen } from '@testing-library/react';
import PublishPage from './page';
import { publishAppPath, wwwPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

type MockUser = {
  is_org_user?: boolean;
  is_single_org_user?: boolean;
  is_agent_user?: boolean;
  organisation_id?: number | null;
};

const setUser = (user: MockUser | null) => {
  (useAuth as jest.Mock).mockReturnValue({ user });
};

describe('PublishPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the publish landing content', () => {
    setUser(null);

    render(<PublishPage />);

    expect(screen.getByRole('heading', { name: 'Publish bus open data' })).toBeInTheDocument();
    expect(screen.getByText('Bus routes and timetable')).toBeInTheDocument();
    expect(screen.getByText('Automatic Vehicle Location (AVL)')).toBeInTheDocument();
    expect(screen.getByText('Fares')).toBeInTheDocument();
  });

  it.each([
    [
      'single-organisation users with an organisation id',
      {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: 123,
      },
      publishAppPath('/org/123/dataset'),
      publishAppPath('/org/123/dataset/fares'),
    ],
    [
      'single-organisation users without an organisation id',
      {
        is_org_user: true,
        is_single_org_user: true,
        is_agent_user: false,
        organisation_id: null,
      },
      publishAppPath('/org'),
      publishAppPath('/org'),
    ],
    [
      'multi-organisation users',
      {
        is_org_user: true,
        is_single_org_user: false,
        is_agent_user: true,
        organisation_id: 123,
      },
      publishAppPath('/org'),
      publishAppPath('/agent-dashboard'),
    ],
  ])(
    'uses the expected dashboard links for %s',
    (_scenario, user, expectedPublishHref, expectedReviewHref) => {
      setUser(user);

      render(<PublishPage />);

      expect(screen.getByRole('link', { name: 'Publish data' })).toHaveAttribute('href', expectedPublishHref);
      expect(screen.getByRole('link', { name: 'Review my data' })).toHaveAttribute('href', expectedReviewHref);
    },
  );

  it('renders the supporting navigation links', () => {
    setUser(null);

    render(<PublishPage />);

    expect(screen.getByRole('link', { name: 'Guide me' })).toHaveAttribute('href', publishAppPath('/guide-me'));
    expect(screen.getByRole('link', { name: 'Manage your account' })).toHaveAttribute('href', publishAppPath('/account'));
    expect(screen.getByRole('link', { name: 'Service changelog' })).toHaveAttribute('href', wwwPath('/changelog'));
    expect(screen.getByRole('link', { name: 'Contact us for technical issues' })).toHaveAttribute('href', wwwPath('/contact'));
  });
});
