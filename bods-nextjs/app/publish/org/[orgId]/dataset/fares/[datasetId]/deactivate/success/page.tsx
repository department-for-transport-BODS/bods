'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresDeactivateSuccessContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const datasetName = searchParams.get('name') || '';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper govuk-!-margin-top-6 govuk-!-margin-bottom-9">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Data set has been deactivated</h1>
            <p className="govuk-body">
              Data set {datasetName} has been deactivated.
            </p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
            <Link role="button" className="govuk-button" href={faresListUrl}>
              Go back to your data sets
            </Link>
          </div>
        </div>
        <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
      </div>
    </div>
  );
}

export default function FaresDeactivateSuccessPage() {
  return (
    <ProtectedRoute>
      <Suspense>
        <FaresDeactivateSuccessContent />
      </Suspense>
    </ProtectedRoute>
  );
}
