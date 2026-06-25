'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function AvlDeleteSuccessPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Data feed has been deleted</h1>
            <p className="govuk-body-l">Data feed has been deleted.</p>
            <Link role="button" className="govuk-button govuk-!-margin-top-5" href={listUrl}>
              Go back to your data feeds
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AvlDeleteSuccessPage() {
  return (
    <ProtectedRoute>
      <AvlDeleteSuccessPageContent />
    </ProtectedRoute>
  );
}
