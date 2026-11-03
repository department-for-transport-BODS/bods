'use client';

/**
 * Feedback sent confirmation (data host, `/operators/<pk>/contact/success/`)
 *
 * Source: transit_odp/browse/templates/browse/operators/contact_operator_success.html
 */

import Link from 'next/link';
import { useEffect } from 'react';
import { operatorsListUrl } from '@/lib/operators';

export function ContactOperatorSuccessContent() {
  useEffect(() => {
    document.title = 'Feedback sent';
  }, []);

  return (
    <div className="govuk-width-container">
      <Link className="govuk-back-link" href={operatorsListUrl()}>
        Back
      </Link>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l app-!-mb-4">Your feedback has been submitted</h1>
            <div className="btn-group-justified">
              <Link role="button" className="govuk-button app-!-mr-sm-4" href={operatorsListUrl()}>
                Go back to operators list
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
