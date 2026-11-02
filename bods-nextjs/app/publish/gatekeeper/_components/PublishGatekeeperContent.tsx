'use client';

/**
 * Publish gatekeeper
 *
 * Shown to consumer (non-organisation) users. Source: PublishGateKeeperView
 * (transit_odp/publish/views/gatekeeper.py), template publish/gatekeeper.html.
 * The Django view has no login requirement, so neither does this page.
 */

import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS, dataPath, publishPath } from '@/config/client';
import { useAuth } from '@/hooks/useAuth';

// Mirrors transit_odp.users.constants.AccountType
const SITE_ADMIN_ACCOUNT_TYPE = 1;
const DEVELOPER_ACCOUNT_TYPE = 4;

export function PublishGatekeeperContent() {
  const { user, isAuthenticated, isLoading } = useAuth();

  let accountMessage: React.ReactNode = null;
  if (!isLoading && !isAuthenticated) {
    accountMessage = (
      <>
        <Link className="govuk-link" href={publishPath('/account/login/')}>
          Please login if you are an operator{' '}
        </Link>
        .
      </>
    );
  } else if (user?.account_type === DEVELOPER_ACCOUNT_TYPE) {
    accountMessage = 'As a developer you can access and use these data sets.';
  } else if (user?.account_type === SITE_ADMIN_ACCOUNT_TYPE) {
    accountMessage = 'As a site admin you can manage organisations and accounts.';
  }

  return (
    <>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: HOSTS.www },
            { label: 'Publish Open Data Service', href: HOSTS.publish },
          ]}
        />
      </div>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-l">Publish your data</h1>
              <p className="govuk-body-l">Only bus operators and local authorities are able to provide their data.</p>
              <p className="govuk-body-l">{accountMessage}</p>
              <Link role="button" className="govuk-button" href={dataPath('/')}>
                Find open data
              </Link>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
