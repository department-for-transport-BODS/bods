'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';

interface ReviewStatusResponse {
  name?: string;
  hasLiveRevision?: boolean;
  status?: string;
}

function FaresDeletePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const datasetUrl = publishAppPath(`/org/${orgId}/dataset/fares/${datasetId}`);

  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [datasetName, setDatasetName] = useState('');
  const [hasLiveRevision, setHasLiveRevision] = useState(false);
  const [liveRevisionStatus, setLiveRevisionStatus] = useState('');

  useEffect(() => {
    const statusUrl = `/api/publish/fares/review-status/${orgId}/${datasetId}/`;
    api
      .get<ReviewStatusResponse>(statusUrl)
      .then(async (data) => {
        setDatasetName(data.name || '');
        const hasLive = Boolean(data.hasLiveRevision);
        setHasLiveRevision(hasLive);
        if (hasLive) {
          // Django's cancel target depends on the live revision's status.
          const live = await api.get<ReviewStatusResponse>(`${statusUrl}?revision=live`);
          setLiveRevisionStatus(live.status || '');
        }
      })
      .catch(() => {});
  }, [orgId, datasetId]);

  // Mirrors fares/feed_delete.html (back link) and RevisionDeleteFaresView.get_cancel_url.
  const backUrl = hasLiveRevision ? datasetUrl : `${datasetUrl}/review`;
  let cancelUrl = `${datasetUrl}/review`;
  if (hasLiveRevision) {
    cancelUrl = liveRevisionStatus === 'expired' ? datasetUrl : `${datasetUrl}/update/review`;
  }

  const heading = hasLiveRevision
    ? 'Would you like to cancel updating this data set'
    : 'Would you like to delete this data set?';

  const bodyText = hasLiveRevision
    ? `Please confirm that you would like to cancel updating data set "${datasetName}" . Any changes you have made so far will not be saved.`
    : `Please confirm that you would like to delete data set "${datasetName}" . Any changes you have made so far will not be saved.`;

  const handleDelete = async () => {
    setErrorMessage('');
    setIsDeleting(true);

    try {
      const data = await api.post<{
        redirect?: string;
        dataset_name?: string;
      }>(`/api/publish/fares/delete/${orgId}/${datasetId}/`);

      const successUrl = `${data.redirect || `/publish/org/${orgId}/dataset/fares/${datasetId}/delete/success`}?name=${encodeURIComponent(data.dataset_name || datasetName)}`;
      globalThis.location.href = successUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to delete data set. Please try again.');
      setIsDeleting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-back-link-wrapper">
        <Link className="govuk-back-link" href={backUrl}>
          Back
        </Link>
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">{heading}</h1>
            <p className="govuk-body-l">{bodyText}</p>

            <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="delete-error-title" />

            <div className="govuk-button-group">
              <button type="button" className="govuk-button" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
              <Link role="button" className="govuk-button govuk-button--secondary" href={cancelUrl}>
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

