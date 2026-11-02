import { render, screen } from '@testing-library/react';
import { SeasonalServiceBreadcrumbs, djangoTitle, pageQuery, seasonalServicesApiPath } from './shared';

describe('seasonal services shared helpers', () => {
  it('mirrors the Django title filter', () => {
    expect(djangoTitle('Review ACME BUS LTD')).toBe('Review Acme Bus Ltd');
    expect(djangoTitle("review o'neill buses")).toBe("Review O'Neill Buses");
    expect(djangoTitle("review dave's buses")).toBe("Review Dave's Buses");
  });

  it('keeps the list page the way Django does', () => {
    expect(pageQuery('2')).toBe('?page=2&');
    expect(pageQuery(null)).toBe('?page=&');
  });

  it('builds the API path for an organisation', () => {
    expect(seasonalServicesApiPath('55')).toBe('/api/publish/seasonal-services/55/');
    expect(seasonalServicesApiPath('55', 'licences/')).toBe('/api/publish/seasonal-services/55/licences/');
  });

  it('labels the review crumb for agent users with the organisation name', () => {
    render(
      <SeasonalServiceBreadcrumbs
        orgId="55"
        organisation={{ organisationId: 55, organisationName: 'zz bus company', isAgentUser: true }}
      />,
    );

    expect(screen.getByRole('link', { name: 'Review Zz Bus Company Timetables Data' })).toBeInTheDocument();
  });
});
