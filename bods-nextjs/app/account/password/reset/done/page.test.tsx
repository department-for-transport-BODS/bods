import { render, screen } from '@testing-library/react';
import { HostProvider } from '@/lib/bods-host-context';
import PasswordResetDonePage from './page';

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <PasswordResetDonePage />
    </HostProvider>,
  );
}

describe('Password reset done page', () => {
  beforeEach(() => {
    window.sessionStorage.clear();
  });

  it('renders the Django sent-email copy with the stashed address', () => {
    window.sessionStorage.setItem('bods:password-reset-email', 'user@example.com');

    renderPage();

    expect(
      screen.getByRole('heading', { name: 'Reset password link has been sent' }),
    ).toBeInTheDocument();
    expect(screen.getByText(/user@example.com/)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Home' })).toBeInTheDocument();
  });

  it('falls back to "you" when no address was stashed', () => {
    renderPage();

    expect(screen.getByText(/sent a password reset email to you\./)).toBeInTheDocument();
  });
});
