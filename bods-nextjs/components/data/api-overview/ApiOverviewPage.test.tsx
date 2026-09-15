import { render, screen } from '@testing-library/react';
import { dataPath } from '@/config/client';
import { ApiOverviewPage } from './ApiOverviewPage';
import { API_OVERVIEWS } from './config';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => children,
}));

describe('ApiOverviewPage', () => {
  it.each(Object.values(API_OVERVIEWS))('renders the $title overview', (config) => {
    render(<ApiOverviewPage config={config} />);

    expect(screen.getByRole('heading', { level: 1, name: config.title })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: config.tryApiLabel })).toHaveAttribute(
      'href',
      dataPath(config.openApiHref),
    );
    expect(screen.getByRole('link', { name: 'Account Settings' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
    if ('description' in config) {
      expect(screen.getByText(config.description)).toBeInTheDocument();
    }
  });

  it('shows subscription journeys only on the location overview', () => {
    const { rerender } = render(<ApiOverviewPage config={API_OVERVIEWS.location} />);

    expect(
      screen.getByRole('heading', { name: 'Subscribe to the Location data API?' }),
    ).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Create Location Data Subscription' })).toHaveAttribute(
      'href',
      dataPath('/api/buslocation-api/subscribe/'),
    );
    expect(screen.getByRole('link', { name: 'Manage subscriptions' })).toHaveAttribute(
      'href',
      dataPath('/api/buslocation-api/manage-subscriptions/'),
    );

    rerender(<ApiOverviewPage config={API_OVERVIEWS.disruptions} />);
    expect(
      screen.queryByRole('heading', { name: 'Subscribe to the Location data API?' }),
    ).not.toBeInTheDocument();
  });

});