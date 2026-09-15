import { render, screen } from '@testing-library/react';
import { dataPath } from '@/config/client';
import ApiServicesPage from './page';

jest.mock('@/components/auth/ProtectedRoute', () => ({
  ProtectedRoute: ({ children }: { children: React.ReactNode }) => children,
}));

describe('ApiServicesPage', () => {
  it('links to every API service at its legacy URL', () => {
    render(<ApiServicesPage />);

    expect(screen.getByRole('heading', { level: 1, name: 'API services' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Timetables data API' })).toHaveAttribute(
      'href',
      dataPath('/api/timetable-openapi/'),
    );
    expect(screen.getByRole('link', { name: 'Location data API' })).toHaveAttribute(
      'href',
      dataPath('/api/buslocation-api/'),
    );
    expect(screen.getByRole('link', { name: 'Fares data API' })).toHaveAttribute(
      'href',
      dataPath('/api/fares-openapi/'),
    );
    expect(screen.getByRole('link', { name: 'Disruptions data API' })).toHaveAttribute(
      'href',
      dataPath('/api/disruptions-api-overview/'),
    );
    expect(screen.getByRole('link', { name: 'Cancellations data API' })).toHaveAttribute(
      'href',
      dataPath('/api/cancellations-api-overview/'),
    );
  });

  it('retains the account and support journeys from Django', () => {
    render(<ApiServicesPage />);

    expect(screen.getByRole('link', { name: 'Account Settings' })).toHaveAttribute(
      'href',
      '/account/settings',
    );
    expect(screen.getByRole('link', { name: 'Guide me' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Service changelog' })).toBeInTheDocument();
    expect(screen.getByRole('link', { name: 'Contact us for technical issues' })).toBeInTheDocument();
  });
});