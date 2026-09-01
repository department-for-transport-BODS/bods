import { render, screen } from '@testing-library/react';
import { HostProvider } from '@/lib/bods-host-context';
import LogoutSuccessPage from './page';

function renderPage() {
  return render(
    <HostProvider hostname="data.xyz.com">
      <LogoutSuccessPage />
    </HostProvider>,
  );
}

describe('Logout success page', () => {
  it('renders the Django signed-out copy and a homepage link', () => {
    renderPage();

    expect(screen.getByRole('heading', { name: 'Signed out' })).toBeInTheDocument();
    expect(
      screen.getByText('You have successfully signed out from your account'),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Return to the homepage' })).toBeInTheDocument();
  });
});
