'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function AVLErrorPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <hr className="govuk-section-break govuk-section-break--m govuk-section-break" />
            <div
              className="govuk-error-summary govuk-!-margin-bottom-0"
              aria-labelledby="error-summary-title"
              role="alert"
              tabIndex={-1}
              data-module="govuk-error-summary"
            >
              <h2 className="govuk-error-summary__title govuk-!-margin-bottom-2" id="error-summary-title">
                Your changes could not be published
              </h2>
              <div className="govuk-error-summary__body">
                <ul className="govuk-list govuk-error-summary__list">
                  <li className="no-underline-l app-error-summary__item">Something went wrong. Please try again later.</li>
                </ul>
              </div>
            </div>
            <div className="govuk-!-padding-bottom-7 govuk-!-padding-top-5">
              <Link
                role="button"
                className="govuk-button govuk-!-margin-bottom-0"
                href={`/publish/org/${orgId}/dataset/avl/${datasetId}/review`}
              >
                Go back to review page
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AVLErrorPage() {
  return (
    <ProtectedRoute>
      <AVLErrorPageContent />
    </ProtectedRoute>
  );
}
