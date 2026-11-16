'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresDeleteSuccessContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const datasetName = searchParams.get('name') || '';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Data set has been deleted</h1>
            <p className="govuk-body">
              {datasetName ? `Data set "${datasetName}" has been deleted.` : 'Data set has been deleted.'}
            </p>
            <Link role="button" className="govuk-button" href={faresListUrl}>
              Go back to your data sets
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresDeleteSuccessPage() {
  return (
    <ProtectedRoute>
      <Suspense>
        <FaresDeleteSuccessContent />
      </Suspense>
    </ProtectedRoute>
  );
}
