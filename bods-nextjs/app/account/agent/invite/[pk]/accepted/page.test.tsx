import { render, screen } from '@testing-library/react';
import { HostProvider } from '@/lib/bods-host-context';
import { api } from '@/lib/api-client';
import AgentInviteAcceptedPage from './page';

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
  useParams: () => ({ pk: '4' }),
}));

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/lib/api-client', () => {
  const actual = jest.requireActual('@/lib/api-client');
  return { ...actual, api: { get: jest.fn() } };
});

describe('Agent invite accepted page', () => {
  it('renders the Django accepted-agent copy', async () => {
    (api.get as jest.Mock).mockResolvedValue({ organisationName: 'Acme Buses' });

    render(
      <HostProvider hostname="publish.xyz.com">
        <AgentInviteAcceptedPage />
      </HostProvider>,
    );

    expect(
      await screen.findByRole('heading', {
        name: 'You are now acting as an agent on behalf of Acme Buses',
      }),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Return to My account' })).toHaveAttribute(
      'href',
      '/account',
    );
  });
});
