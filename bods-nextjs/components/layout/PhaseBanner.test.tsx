import { render, screen } from '@testing-library/react';
import { wwwPath } from '@/config/client';
import { PhaseBanner } from './PhaseBanner';

let mockPathname = '/changelog';

jest.mock('next/navigation', () => ({
  usePathname: () => mockPathname,
}));

function setLocation(url: string) {
  window.history.pushState({}, '', url);
}

describe('PhaseBanner', () => {
  beforeEach(() => {
    mockPathname = '/changelog';
    setLocation('/changelog');
  });

  it("links to Django's global-feedback page with ?url=<host><path>", () => {
    render(<PhaseBanner />);

    expect(screen.getByRole('link', { name: 'feedback' })).toHaveAttribute(
      'href',
      `${wwwPath('/global-feedback/')}?url=${window.location.host}/changelog`,
    );
  });

  it('url-encodes the query string like the Django urlencode filter', () => {
    setLocation('/search?q=bus&page=2');
    render(<PhaseBanner />);

    expect(screen.getByRole('link', { name: 'feedback' })).toHaveAttribute(
      'href',
      `${wwwPath('/global-feedback/')}?url=${window.location.host}/search%3Fq%3Dbus%26page%3D2`,
    );
  });

  it('renders plain text on the global feedback page, as Django does', () => {
    mockPathname = '/global-feedback';
    render(<PhaseBanner />);

    expect(screen.queryByRole('link', { name: 'feedback' })).not.toBeInTheDocument();
    expect(screen.getByText(/This is a new service/)).toHaveTextContent(
      'This is a new service – your feedback will help us to improve it.',
    );
  });

  it('renders plain text when hideGlobalFeedback is set', () => {
    render(<PhaseBanner hideGlobalFeedback />);

    expect(screen.queryByRole('link', { name: 'feedback' })).not.toBeInTheDocument();
  });
});
