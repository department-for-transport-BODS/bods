import { render, screen } from '@testing-library/react';
import ChangePasswordDonePage from './page';

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

describe('Change password done page', () => {
  it('renders the Django success copy and a link back to settings', () => {
    render(<ChangePasswordDonePage />);

    expect(screen.getByRole('heading', { name: 'Change password' })).toBeInTheDocument();
    expect(screen.getByText('Your password has been updated.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Go back to account settings' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
  });
});
