'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';

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
    api
      .get<{ name?: string; hasLiveRevision?: boolean }>(
        `/api/fares/review-status/${orgId}/${datasetId}/`,
      )
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
      const data = await api.post<{
        redirect?: string;
        dataset_name?: string;
      }>(`/api/fares/delete/${orgId}/${datasetId}/`);

      const successUrl = `${data.redirect || `/publish/org/${orgId}/dataset/fares/${datasetId}/delete/success`}?name=${encodeURIComponent(data.dataset_name || datasetName)}`;
      globalThis.location.href = successUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to delete data set. Please try again.');
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

            <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="delete-error-title" />

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

