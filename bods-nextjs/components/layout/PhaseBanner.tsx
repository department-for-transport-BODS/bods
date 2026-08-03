/**
 * Phase Banner Component
 *
 * Displays the BETA phase banner at the top of the page.
 * Source: transit_odp/templates/banner.html
 * TODO: At a later date this should be replaced with an off the shelf lib component that can be shared across the estate
 */

import Link from 'next/link';

interface PhaseBannerProps {
  hideGlobalFeedback?: boolean;
}

export function PhaseBanner({ hideGlobalFeedback = false }: PhaseBannerProps) {

  return (
    <div className="govuk-phase-banner">
      <p className="govuk-phase-banner__content">
        <strong className="govuk-tag govuk-phase-banner__content__tag">BETA</strong>
        <span className="govuk-phase-banner__text">
          This is a new service – your{' '}
          {hideGlobalFeedback ? (
            'feedback'
          ) : (
            <Link href="/feedback" className="govuk-link">
              feedback
            </Link>
          )}{' '}
          will help us to improve it.
        </span>
      </p>
    </div>
  );
}

