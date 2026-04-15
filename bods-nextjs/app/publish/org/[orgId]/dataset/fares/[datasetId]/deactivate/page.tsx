'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

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
      const token = globalThis.window
        ? globalThis.window.localStorage.getItem('bods.auth.access')
        : null;

      const response = await fetch(`/api/fares/deactivate?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const data = (await response.json().catch(() => ({}))) as {
        error?: string;
        redirect?: string;
        deactivated?: boolean;
        dataset_name?: string;
      };

      if (!response.ok) {
        setErrorMessage(data.error || `Deactivate failed (${response.status}).`);
        setIsDeactivating(false);
        return;
      }

      const successUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/deactivate/success?name=${encodeURIComponent(data.dataset_name || '')}`;
      globalThis.location.href = successUrl;
    } catch {
      setErrorMessage('Unable to deactivate data set. Please try again.');
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

            {errorMessage ? (
              <div className="govuk-error-summary" role="alert" aria-labelledby="deactivate-error-title">
                <h2 className="govuk-error-summary__title" id="deactivate-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{errorMessage}</li>
                  </ul>
                </div>
              </div>
            ) : null}

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
