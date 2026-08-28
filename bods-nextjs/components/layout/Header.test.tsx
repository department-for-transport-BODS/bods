import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useAuth } from '@/hooks/useAuth';
import type { User } from '@/types';
import { Header } from './Header';
import { HostProvider } from '@/lib/bods-host-context';

jest.mock('@/hooks/useAuth', () => ({
  useAuth: jest.fn(),
}));

const orgAdmin: User = {
  id: 1,
  email: 'admin@example.com',
  organisation_id: 12,
  is_org_admin: true,
};

const orgStaff: User = {
  id: 2,
  email: 'staff@example.com',
  organisation_id: 12,
  is_org_admin: false,
};

const developer: User = {
  id: 3,
  email: 'dev@example.com',
  organisation_id: null,
  is_org_admin: false,
};

function setUser(user: User | null) {
  (useAuth as jest.Mock).mockReturnValue({ user });
}

function renderHeader(hostname: string) {
  return render(
    <HostProvider hostname={hostname}>
      <Header />
    </HostProvider>,
  );
}

async function openAccountMenu() {
  await userEvent.click(screen.getByRole('button', { name: /My account/ }));
}

describe('Header account menu', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('shows publish menu items for organisation admins', async () => {
    setUser(orgAdmin);

    renderHeader('publish.xyz.com');
    await openAccountMenu();

    expect(screen.getByRole('link', { name: 'My account' })).toHaveAttribute('href', '/account');
    expect(screen.getByRole('link', { name: 'User management' })).toHaveAttribute(
      'href',
      '/account/manage/12',
    );
    expect(screen.getByRole('link', { name: 'Organisation profile' })).toHaveAttribute(
      'href',
      '/account/manage/org-profile/12',
    );
    expect(screen.getByRole('link', { name: 'Account settings' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
    expect(screen.getByRole('link', { name: 'Sign out' })).toHaveAttribute('href', '/account/logout');
    expect(screen.queryByRole('link', { name: 'Manage subscriptions' })).not.toBeInTheDocument();
  });

  it('hides user management on publish for non-admin organisation users', async () => {
    setUser(orgStaff);

    renderHeader('publish.xyz.com');
    await openAccountMenu();

    expect(screen.getByRole('link', { name: 'My account' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'User management' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Organisation profile' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Account settings' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign out' })).toBeInTheDocument();
  });

  it('hides organisation profile on publish when the user has no organisation', async () => {
    setUser(developer);

    renderHeader('publish.xyz.com');
    await openAccountMenu();

    expect(screen.getByRole('link', { name: 'My account' })).toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'User management' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Organisation profile' })).not.toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Account settings' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign out' })).toBeInTheDocument();
  });

  it('shows find menu items including manage subscriptions', async () => {
    setUser(orgAdmin);

    renderHeader('data.xyz.com');
    await openAccountMenu();

    expect(screen.getByRole('link', { name: 'My account' })).toHaveAttribute('href', '/account');
    expect(screen.getByRole('link', { name: 'Manage subscriptions' })).toHaveAttribute(
      'href',
      '/account/manage',
    );
    expect(screen.getByRole('link', { name: 'Account settings' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
    expect(screen.getByRole('link', { name: 'Sign out' })).toHaveAttribute('href', '/account/logout');
    expect(screen.queryByRole('link', { name: 'User management' })).not.toBeInTheDocument();
    expect(screen.queryByRole('link', { name: 'Organisation profile' })).not.toBeInTheDocument();
  });

  it('shows sign in when the user is signed out', () => {
    setUser(null);

    renderHeader('data.xyz.com');

    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/account/login');
    expect(screen.queryByRole('button', { name: /My account/ })).not.toBeInTheDocument();
  });
});

describe('Header service navigation', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    setUser(null);
  });

  it.each(['publish.xyz.com', 'data.xyz.com'])(
    'keeps the guide me link on the current host (%s)',
    (hostname) => {
      renderHeader(hostname);

      expect(screen.getByRole('link', { name: 'Guide me' })).toHaveAttribute(
        'href',
        '/guide-me',
      );
    },
  );

  it('hides the service navigation on www', () => {
    renderHeader('xyz.com');

    expect(screen.queryByRole('link', { name: 'Guide me' })).not.toBeInTheDocument();
  });
});
