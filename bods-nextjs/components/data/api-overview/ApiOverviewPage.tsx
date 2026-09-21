import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { DataHelpSidebar } from '@/components/data/DataHelpSidebar';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import type { ApiOverviewConfig } from './config';

export function ApiOverviewPage({ config }: { config: ApiOverviewConfig }) {
  return (
    <ProtectedRoute>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={hostBreadcrumbs(
            'data',
            { label: 'API services', href: dataPath('/api/') },
            { label: config.title, current: true },
          )}
        />
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl">{config.title}</h1>
              <section className="govuk-!-margin-bottom-6">
                <h2 className="govuk-heading-m">Ready to use the API?</h2>
                <Link className="govuk-link" href={dataPath('/guidance/requirements')}>
                  View developer documentation
                </Link>
              </section>
              <section className="govuk-!-margin-bottom-6">
                <h2 className="govuk-heading-m">First time API user?</h2>
                <Link className="govuk-link" href={dataPath('/guide-me')}>
                  Guide me
                </Link>
              </section>
              <section className="govuk-!-margin-bottom-6">
                <h2 className="govuk-heading-m">Try API service?</h2>
                <p className="govuk-body">
                  You can experiment with our interactive API services, to familiarise yourself with
                  the data supplied. Please append your API_Key from your{' '}
                  <Link className="govuk-link" href="/account/settings">
                    Account Settings
                  </Link>{' '}
                  page and query parameters to your API requests.
                </p>
                {config.description && <p className="govuk-body">{config.description}</p>}
                <Link className="govuk-link" href={dataPath(config.openApiHref)}>
                  {config.tryApiLabel}
                </Link>
              </section>
              {config.subscriptionLinks && (
                <section className="govuk-!-margin-bottom-6">
                  <h2 className="govuk-heading-m">Subscribe to the Location data API?</h2>
                  <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                    {config.subscriptionLinks.map((link) => (
                      <li key={link.href} className="govuk-!-margin-bottom-4">
                        <Link className="govuk-link" href={dataPath(link.href)}>
                          {link.label}
                        </Link>
                      </li>
                    ))}
                  </ul>
                </section>
              )}
            </div>
            <DataHelpSidebar />
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}