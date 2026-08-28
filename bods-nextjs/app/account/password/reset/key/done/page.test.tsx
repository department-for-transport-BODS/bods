import { render, screen } from '@testing-library/react';
import PasswordResetKeyDonePage from './page';

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

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}));

describe('Password reset from key done page', () => {
  it('renders the Django success copy and a link to My account', () => {
    render(<PasswordResetKeyDonePage />);

    expect(screen.getByRole('heading', { name: 'Password has been reset' })).toBeInTheDocument();
    expect(
      screen.getByText('Your password has been successfully reset and you have been logged in.'),
    ).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'My data account' })).toHaveAttribute('href', '/account');
  });
});
