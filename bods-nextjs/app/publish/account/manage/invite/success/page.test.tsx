import { render, screen } from '@testing-library/react';
import InviteSuccessPage from './page';

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

jest.mock('@/components/auth/OrgAdminRoute', () => ({
  OrgAdminRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

jest.mock('@/hooks/useAuth', () => ({
  useAuth: () => ({ user: { organisation_id: 12 } }),
}));

describe('Invite success page', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it('renders the Django sent-invite copy with the stashed address', () => {
    window.sessionStorage.setItem('bods:invite-email', 'new.user@example.com');

    render(<InviteSuccessPage />);

    expect(screen.getByRole('heading', { name: 'Invitation has been sent' })).toBeInTheDocument();
    expect(screen.getByText(/new.user@example.com/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to user management' })).toHaveAttribute(
      'href',
      '/account/manage/12',
    );
  });
});
