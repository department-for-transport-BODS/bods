import { render, screen } from '@testing-library/react';
import DataGuideMePage from './page';
import { dataPath, HOSTS } from '@/config/client';

describe('DataGuideMePage', () => {
  it('breadcrumbs back through the Find service', () => {
    render(<DataGuideMePage />);

    expect(screen.getByRole('link', { name: 'Bus Open Data Service' })).toHaveAttribute(
      'href',
      HOSTS.www,
    );
    expect(screen.getByRole('link', { name: 'Find Bus Open Data' })).toHaveAttribute(
      'href',
      HOSTS.data,
    );
    expect(screen.getByRole('heading', { level: 1, name: 'Guide me' })).toBeInTheDocument();
  });

  it('lists the Find guidance steps', () => {
    render(<DataGuideMePage />);

    const stepTitles = screen
      .getAllByRole('heading', { level: 2 })
      .map((heading) => heading.textContent);

    expect(stepTitles).toEqual(
      expect.arrayContaining([
        expect.stringContaining('Read supporting documents'),
        expect.stringContaining('See what is on BODS'),
        expect.stringContaining('Get an account'),
        expect.stringContaining('Use download'),
        expect.stringContaining('Use API'),
      ]),
    );
  });

  it('links to the Find pages each step describes', () => {
    render(<DataGuideMePage />);

    expect(screen.getByRole('link', { name: 'Browse data' })).toHaveAttribute(
      'href',
      dataPath('/search'),
    );
    expect(screen.getByRole('link', { name: 'API services' })).toHaveAttribute(
      'href',
      dataPath('/api'),
    );
    expect(screen.getByRole('link', { name: 'Register your account' })).toHaveAttribute(
      'href',
      '/account/signup',
    );
    expect(screen.getByRole('link', { name: 'Get my API key' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
  });

  it('opens third party guidance in a new tab', () => {
    render(<DataGuideMePage />);

    const extractor = screen.getByRole('link', { name: 'BODS Data Extractor Python Package' });

    expect(extractor).toHaveAttribute('target', '_blank');
    expect(extractor).toHaveAttribute('rel', expect.stringContaining('noopener'));
  });
});
