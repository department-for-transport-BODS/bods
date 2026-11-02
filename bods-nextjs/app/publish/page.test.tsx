import { render, screen, within } from '@testing-library/react';
import PublishPage, { metadata } from './page';
import { HOSTS, publishAppPath, wwwPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

const replace = jest.fn();
jest.mock('next/navigation', () => ({
  useRouter: () => ({ push: jest.fn(), replace }),
}));

type MockUser = {
  account_type?: number;
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

  it('uses the Django page title', () => {
    expect(metadata.title).toBe('Publish bus open data');
  });

  it('links both breadcrumbs like Django', () => {
    setUser(null);

    render(<PublishPage />);

    const breadcrumbs = within(screen.getByRole('navigation', { name: 'Breadcrumb' }));
    const links = breadcrumbs.getAllByRole('link');
    expect(links.map((link) => [link.textContent, link.getAttribute('href')])).toEqual([
      ['Bus Open Data Service', HOSTS.www],
      ['Publish Bus Open Data', HOSTS.publish],
    ]);
  });

  it.each([
    [
      'consumer (developer) users',
      { account_type: 4, is_org_user: false, is_single_org_user: false, is_agent_user: false, organisation_id: null },
      publishAppPath('/gatekeeper'),
      publishAppPath('/gatekeeper'),
    ],
    [
      'consumer (site admin) users',
      { account_type: 1, is_org_user: false, is_single_org_user: false, is_agent_user: false, organisation_id: null },
      publishAppPath('/gatekeeper'),
      publishAppPath('/gatekeeper'),
    ],
    [
      'agent users',
      { account_type: 5, is_org_user: true, is_single_org_user: false, is_agent_user: true, organisation_id: 123 },
      publishAppPath('/org'),
      publishAppPath('/agent-dashboard'),
    ],
    [
      'organisation admin users',
      { account_type: 2, is_org_user: true, is_single_org_user: true, is_agent_user: false, organisation_id: 123 },
      publishAppPath('/org/123/dataset'),
      publishAppPath('/org/123/dataset/timetable'),
    ],
    [
      'organisation staff users',
      { account_type: 3, is_org_user: true, is_single_org_user: true, is_agent_user: false, organisation_id: 456 },
      publishAppPath('/org/456/dataset'),
      publishAppPath('/org/456/dataset/timetable'),
    ],
    [
      'organisation users without an organisation id',
      { account_type: 2, is_org_user: true, is_single_org_user: true, is_agent_user: false, organisation_id: null },
      publishAppPath('/org'),
      publishAppPath('/org'),
    ],
  ])(
    'uses the expected dashboard links for %s',
    (_scenario, user, expectedPublishHref, expectedReviewHref) => {
      setUser(user);

      render(<PublishPage />);

      // Django renders the start link with role="button".
      expect(screen.getByRole('button', { name: 'Publish data' })).toHaveAttribute('href', expectedPublishHref);
      expect(screen.getByRole('link', { name: 'Review my data' })).toHaveAttribute('href', expectedReviewHref);
      expect(replace).not.toHaveBeenCalled();
    },
  );

  it('redirects abods users straight to the abods gatekeeper without rendering the dashboard', () => {
    setUser({ account_type: 6, is_org_user: true, is_single_org_user: false, is_agent_user: false, organisation_id: 9 });

    render(<PublishPage />);

    expect(replace).toHaveBeenCalledWith(publishAppPath('/abods-gatekeeper'));
    expect(screen.queryByRole('heading', { name: 'Publish bus open data' })).not.toBeInTheDocument();
  });

  it('renders the supporting navigation links', () => {
    setUser(null);

    render(<PublishPage />);

    expect(screen.getByRole('link', { name: 'Guide me' })).toHaveAttribute('href', publishAppPath('/guide-me'));
    expect(screen.getByRole('link', { name: 'Manage your account' })).toHaveAttribute('href', '/account');
    expect(screen.getByRole('link', { name: 'Service changelog' })).toHaveAttribute('href', wwwPath('/changelog'));
    expect(screen.getByRole('link', { name: 'Contact us for technical issues' })).toHaveAttribute('href', wwwPath('/contact'));
  });
});
