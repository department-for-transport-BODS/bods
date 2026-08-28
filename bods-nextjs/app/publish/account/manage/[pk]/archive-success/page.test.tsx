import { render, screen } from '@testing-library/react';
import { api } from '@/lib/api-client';
import ArchiveMemberSuccessPage from './page';

jest.mock('next/link', () => {
  return function MockLink({
    children,
    href,
    ...props
  }: {
    children: React.ReactNode;
    href: string;
  }) {
    return (
      <a href={href} {...props}>
        {children}
      </a>
    );
  };
});

jest.mock('next/navigation', () => ({
  useParams: () => ({ pk: '9' }),
}));

jest.mock('@/components/auth/OrgAdminRoute', () => ({
  OrgAdminRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { organisation_id: 12 } }),
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

describe('Archive success page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders the deactivated copy when the member is inactive', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      id: 9,
      username: 'Pat Operator',
      isActive: false,
    });

    render(<ArchiveMemberSuccessPage />);

    expect(await screen.findByRole('heading', { name: 'User has been deactivated' })).toBeInTheDocument();
    expect(
      screen.getByText(
        'User Pat Operator has been deactivated and will no longer have access to the Bus Open Data Service.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to user management' })).toHaveAttribute(
      'href',
      '/account/manage/12',
    );
  });

  it('renders the activated copy when the member is active', async () => {
    (api.get as jest.Mock).mockResolvedValue({
      id: 9,
      username: 'Pat Operator',
      isActive: true,
    });

    render(<ArchiveMemberSuccessPage />);

    expect(await screen.findByRole('heading', { name: 'User has been activated' })).toBeInTheDocument();
    expect(
      screen.getByText(
        'User Pat Operator has been activated and will have access to the Bus Open Data Service.',
      ),
    ).toBeInTheDocument();
  });
});
