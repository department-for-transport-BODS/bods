'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresPublishSuccessContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const datasetDetailUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}`;
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <div className="govuk-panel govuk-panel--confirmation govuk-!-margin-top-9">
              <h1 className="govuk-panel__title">
                Your data set has been successfully published
              </h1>
            </div>

            <p className="govuk-body-m">
              We have sent you a confirmation email.
            </p>

            <h2 className="govuk-heading-m">What happens next?</h2>
            <p className="govuk-body-m">
              You can view the data set on{' '}
              <Link className="govuk-link" href={faresListUrl}>
                your fares data sets
              </Link>{' '}
              or by clicking the button below. The data will now be live for everyone else to see.
            </p>

            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />

            <Link className="govuk-button" href={datasetDetailUrl}>
              View published data set
            </Link>

            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <div className="govuk-grid-column-one-third"></div>
        </div>
      </div>
    </div>
  );
}

export default function FaresPublishSuccessPage() {
  return (
    <ProtectedRoute>
      <FaresPublishSuccessContent />
    </ProtectedRoute>
  );
}
