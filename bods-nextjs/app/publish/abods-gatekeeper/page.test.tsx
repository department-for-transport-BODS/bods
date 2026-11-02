import { render, screen } from '@testing-library/react';
import PublishAbodsGatekeeperPage, { metadata } from './page';
import { HOSTS } from '@/config/client';

describe('PublishAbodsGatekeeperPage', () => {
  it('uses the Django page title', () => {
    expect(metadata.title).toBe('Publish your data');
  });

  it('renders the Django heading, copy and ABODS link', () => {
    render(<PublishAbodsGatekeeperPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'Analyse Bus Open Data' })).toBeInTheDocument();
    expect(screen.getByText('Use this link to navigate to the Analyse Bus Open Data service.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Access ABODS' })).toHaveAttribute(
      'href',
      'https://analyse.bus-data.dft.gov.uk/',
    );
  });

  it('only has the Bus Open Data Service breadcrumb', () => {
    render(<PublishAbodsGatekeeperPage />);

    expect(screen.getByRole('link', { name: 'Bus Open Data Service' })).toHaveAttribute('href', HOSTS.www);
    expect(screen.queryByRole('link', { name: 'Publish Open Data Service' })).not.toBeInTheDocument();
  });
});
