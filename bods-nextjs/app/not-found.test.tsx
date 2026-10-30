import { render, screen } from '@testing-library/react';
import NotFound, { metadata } from './not-found';
import { wwwPath } from '@/config/client';

describe('NotFound', () => {
  it('matches the Django 404 template copy', () => {
    const { container } = render(<NotFound />);

    expect(screen.getByRole('heading', { level: 1, name: 'Page not found' })).toHaveClass(
      'govuk-heading-l',
    );
    expect(
      screen.getByText('If you typed the web address, check it is correct.'),
    ).toBeInTheDocument();
    expect(
      screen.getByText('If you pasted the web address, check you copied the entire address.'),
    ).toBeInTheDocument();
    expect(container).toHaveTextContent(
      'If the web address is correct or you selected a link or button, contact Bus open data support line if you need to speak to someone about this service.',
    );
    expect(
      screen.getByRole('link', { name: 'contact Bus open data support line' }),
    ).toHaveAttribute('href', wwwPath('/contact'));
  });

  it('has no breadcrumbs, like the Django error page', () => {
    render(<NotFound />);

    expect(screen.queryByRole('navigation', { name: 'Breadcrumb' })).not.toBeInTheDocument();
  });

  it('sets the Django page title', () => {
    expect(metadata.title).toBe('Page not found - Bus Open Data Service');
  });
});
