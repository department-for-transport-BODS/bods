'use client';

import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function AVLCreateCancelPageContent() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;

  useEffect(() => {
    document.title = 'Publish new data feed: Cancel step for publish';
  }, []);

  const formUrl = `/publish/org/${orgId}/dataset/avl/new`;
  const listUrl = `/publish/org/${orgId}/dataset/avl`;

  const goBackOrFallback = () => {
    if (globalThis.history.length > 1) {
      router.back();
      return;
    }

    globalThis.location.href = formUrl;
  };

  return (
    <div className="govuk-width-container">
      <Link type="button" className="govuk-back-link govuk-button-back-link" href={formUrl}>
        Back
      </Link>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Would you like to cancel publishing this data feed?</h1>
            <p className="govuk-body">Any changes you have made so far will not be saved.</p>

            <div className="govuk-button-group">
              <Link role="button" className="govuk-button" href={listUrl}>
                Confirm
              </Link>
              <button type="button" className="govuk-button govuk-button--secondary" onClick={goBackOrFallback}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AVLCreateCancelPage() {
  return (
    <ProtectedRoute>
      <AVLCreateCancelPageContent />
    </ProtectedRoute>
  );
}