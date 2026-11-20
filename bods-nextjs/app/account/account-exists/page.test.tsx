import { render, screen } from '@testing-library/react';
import AccountExistsPage from './page';

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

describe('Account exists page', () => {
  it('renders the Django copy and a sign-in button', () => {
    render(<AccountExistsPage />);

    expect(screen.getByRole('heading', { name: 'Account exists' })).toBeInTheDocument();
    expect(
      screen.getByText(
        'An account with this email address has already been registered on BODS. Please click below to sign in.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Sign in' })).toHaveAttribute('href', '/account/login');
  });
});
