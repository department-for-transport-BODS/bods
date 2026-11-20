import { render, screen } from '@testing-library/react';
import { HostProvider } from '@/lib/bods-host-context';
import AccountInactivePage from './page';

describe('Account inactive page', () => {
  it('matches Django account-inactive copy and links to contact on www', () => {
    render(
      <HostProvider hostname="data.xyz.com">
        <AccountInactivePage />
      </HostProvider>,
    );

    expect(screen.getByRole('heading', { name: 'Account Inactive', level: 1 }))
      .toBeInTheDocument();
    expect(screen.getByText(/Your account is inactive and you no longer have access to the Bus Open Data Service\./))
      .toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'contact us' }))
      .toHaveAttribute('href', expect.stringContaining('/contact'));
  });
});
