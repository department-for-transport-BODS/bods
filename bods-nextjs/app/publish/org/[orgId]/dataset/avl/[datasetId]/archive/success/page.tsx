'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function AvlArchiveSuccessPageContent() {
  const params = useParams();
  const searchParams = useSearchParams();

  const orgId = params.orgId as string;
  const datasetName = searchParams.get('name');
  const listUrl = `/publish/org/${orgId}/dataset/avl`;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row govuk-!-margin-top-6 govuk-!-margin-bottom-9">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Data feed has been deactivated</h1>
            <p className="govuk-body">
              {datasetName
                ? `Data feed ${datasetName} has been deactivated.`
                : 'Data feed has been deactivated.'}
            </p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
            <Link role="button" className="govuk-button" href={listUrl}>
              Go back to your data feeds
            </Link>
          </div>
        </div>
        <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
      </div>
    </div>
  );
}

export default function AvlArchiveSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlArchiveSuccessPageContent />
    </ProtectedRoute>
  );
}
