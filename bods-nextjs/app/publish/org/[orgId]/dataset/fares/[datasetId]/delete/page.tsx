'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function FaresDeletePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const reviewUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/review`;

  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [hasLiveRevision, setHasLiveRevision] = useState(false);

  useEffect(() => {
    const token = globalThis.window
      ? globalThis.window.localStorage.getItem('bods.auth.access')
      : null;
    if (!token) return;

    fetch(`/api/fares/review-status?orgId=${orgId}&datasetId=${datasetId}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.json())
      .then((data: { name?: string; hasLiveRevision?: boolean }) => {
        setDatasetName(data.name || '');
        setHasLiveRevision(Boolean(data.hasLiveRevision));
      })
      .catch(() => {});
  }, [orgId, datasetId]);

  const heading = hasLiveRevision
    ? 'Would you like to cancel updating this data set'
    : 'Would you like to delete this data set?';

  const bodyText = hasLiveRevision
    ? `Please confirm that you would like to cancel updating data set "${datasetName}". Any changes you have made so far will not be saved.`
    : `Please confirm that you would like to delete data set "${datasetName}". Any changes you have made so far will not be saved.`;

  const handleDelete = async () => {
    setErrorMessage('');
    setIsDeleting(true);

    try {
      const token = globalThis.window
        ? globalThis.window.localStorage.getItem('bods.auth.access')
        : null;

      const response = await fetch(`/api/fares/delete?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        headers: token ? { Authorization: `Bearer ${token}` } : {},
      });

      const data = (await response.json().catch(() => ({}))) as {
        error?: string;
        redirect?: string;
        deleted?: boolean;
        dataset_name?: string;
      };

      if (!response.ok) {
        setErrorMessage(data.error || `Delete failed (${response.status}).`);
        setIsDeleting(false);
        return;
      }

      const successUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/delete/success?name=${encodeURIComponent(data.dataset_name || datasetName)}`;
      globalThis.location.href = successUrl;
    } catch {
      setErrorMessage('Unable to delete data set. Please try again.');
      setIsDeleting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-back-link-wrapper">
          <Link className="govuk-back-link" href={reviewUrl}>
            Back
          </Link>
        </div>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">{heading}</h1>
            <p className="govuk-body-l">{bodyText}</p>

            {errorMessage ? (
              <div className="govuk-error-summary" role="alert" aria-labelledby="delete-error-title">
                <h2 className="govuk-error-summary__title" id="delete-error-title">
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
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
              <Link className="govuk-link" href={reviewUrl}>
                Cancel
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresDeletePage() {
  return (
    <ProtectedRoute>
      <FaresDeletePageContent />
    </ProtectedRoute>
  );
}

