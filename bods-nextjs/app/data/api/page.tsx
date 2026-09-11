import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath, wwwPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

const API_SERVICES = [
  { label: 'Timetables data API', href: '/api/timetable-openapi/' },
  { label: 'Location data API', href: '/api/buslocation-api/' },
  { label: 'Fares data API', href: '/api/fares-openapi/' },
  { label: 'Disruptions data API', href: '/api/disruptions-api-overview/' },
  { label: 'Cancellations data API', href: '/api/cancellations-api-overview/' },
] as const;

export const metadata = {
  title: 'API services - Bus Open Data Service',
  description: 'Explore the interactive APIs available through the Bus Open Data Service.',
};

export default function ApiServicesPage() {
  return (
    <ProtectedRoute>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={hostBreadcrumbs('data', { label: 'API services', current: true })}
        />
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">API services</h1>
              <p className="govuk-body govuk-!-padding-bottom-3">
                You can experiment with our interactive API services to, familiarise yourself with
                the data supplied. Please append your API_Key from your{' '}
                <Link className="govuk-link" href="/account/settings">
                  Account Settings
                </Link>{' '}
                page and query parameters to your API requests.
              </p>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                {API_SERVICES.map((service) => (
                  <li key={service.href} className="govuk-!-margin-bottom-4">
                    <Link className="govuk-link-bold" href={dataPath(service.href)}>
                      {service.label}
                    </Link>
                  </li>
                ))}
              </ul>
            </div>
            <div className="govuk-grid-column-one-third">
              <h2 className="govuk-heading-m">Need further help?</h2>
              <ul className="govuk-list">
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href={dataPath('/guide-me')}>
                    Guide me
                  </Link>
                </li>
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href={wwwPath('/changelog')}>
                    Service changelog
                  </Link>
                </li>
                <li className="govuk-!-margin-bottom-3">
                  <Link className="govuk-link" href={wwwPath('/contact')}>
                    Contact us for technical issues
                  </Link>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}