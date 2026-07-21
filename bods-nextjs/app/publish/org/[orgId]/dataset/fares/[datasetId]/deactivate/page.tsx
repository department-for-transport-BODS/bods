'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';

function FaresDeactivatePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const detailUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}`;

  const [isDeactivating, setIsDeactivating] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const handleConfirm = async () => {
    setErrorMessage('');
    setIsDeactivating(true);

    try {
      const data = await api.post<{
        deactivated?: boolean;
        dataset_name?: string;
      }>(`/api/fares/deactivate/${orgId}/${datasetId}/`);

      const successUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/deactivate/success?name=${encodeURIComponent(data.dataset_name || '')}`;
      globalThis.location.href = successUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to deactivate data set. Please try again.');
      setIsDeactivating(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-back-link-wrapper">
          <Link className="govuk-back-link" href={detailUrl}>
            Back
          </Link>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-three-quarters">
            <h1 className="govuk-heading-xl">Would you like to deactivate this data set?</h1>
            <p className="govuk-body">
              Deactivating this data set means that this data set is no longer active. Inactive data sets can
              still be viewed and used by data consumers.
            </p>

            <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="deactivate-error-title" />

            <div className="govuk-button-group">
              <button
                type="button"
                className="govuk-button app-!-mr-sm-4"
                onClick={handleConfirm}
                disabled={isDeactivating}
              >
                {isDeactivating ? 'Deactivating...' : 'Confirm'}
              </button>
              <Link className="govuk-button govuk-button--secondary" href={detailUrl}>
                Cancel
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresDeactivatePage() {
  return (
    <ProtectedRoute>
      <FaresDeactivatePageContent />
    </ProtectedRoute>
  );
}
