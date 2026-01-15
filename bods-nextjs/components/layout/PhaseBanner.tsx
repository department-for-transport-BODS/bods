/**
 * Phase Banner Component
 *
 * Displays the BETA phase banner at the top of the page.
 * Source: transit_odp/templates/banner.html
 * Replace this with a GDS component - These exist
 */

import Link from 'next/link';

export function PhaseBanner() {
  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">BETA</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your{' '}
          <Link href="/feedback" className="govuk-link">
            feedback
          </Link>{' '}
          will help us to improve it.
        </span>
      </p>
    </div>
  );
}

