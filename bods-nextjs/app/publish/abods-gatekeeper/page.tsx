/**
 * Publish ABODS gatekeeper
 *
 * Shown to abods users instead of the publish journeys. Source:
 * PublishAbodsGateKeeperView (transit_odp/publish/views/gatekeeper.py),
 * template publish/abods-gatekeeper.html. No login requirement in Django.
 */

import type { Metadata } from 'next';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { HOSTS } from '@/config/client';

export const metadata: Metadata = {
  title: 'Publish your data',
};

export default function PublishAbodsGatekeeperPage() {
  return (
    <>
      <div className="govuk-width-container">
        <Breadcrumbs items={[{ label: 'Bus Open Data Service', href: HOSTS.www }]} />
      </div>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-l">Analyse Bus Open Data</h1>
              <p className="govuk-body-l">Use this link to navigate to the Analyse Bus Open Data service.</p>
              <a role="button" className="govuk-button" href="https://analyse.bus-data.dft.gov.uk/">
                Access ABODS
              </a>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
