'use client';

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';

type AvlDeleteContext = {
  name?: string;
  hasLiveRevision?: boolean;
};

function AvlDeletePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoadingContext, setIsLoadingContext] = useState(true);
  const [datasetName, setDatasetName] = useState('');
  const [hasLiveRevision, setHasLiveRevision] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const reviewUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/review`;
  const updateReviewUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update/review`;
  const fallbackSuccessUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/delete/success`;

  useEffect(() => {
    let cancelled = false;

    const loadContext = async () => {
      try {
        const data = await api.get<AvlDeleteContext>(`/api/avl/review-status/${orgId}/${datasetId}/`);
        if (!cancelled) {
          setDatasetName(data.name || '');
          setHasLiveRevision(Boolean(data.hasLiveRevision));
          setIsLoadingContext(false);
        }
      } catch {
        if (!cancelled) {
          setIsLoadingContext(false);
        }
      }
    };

    loadContext();

    return () => {
      cancelled = true;
    };
  }, [datasetId, orgId]);

  const handleDelete = async () => {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const data = await api.post<{ redirect?: string }>(`/api/avl/delete/${orgId}/${datasetId}/`);
      globalThis.location.href = data.redirect || fallbackSuccessUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to delete data feed. Please try again.');
      setIsSubmitting(false);
    }
  };

  const heading = hasLiveRevision
    ? 'Would you like to cancel updating this data feed'
    : 'Would you like to delete this data feed?';
  const contextAction = hasLiveRevision ? 'cancel updating data feed' : 'delete data feed';
  const cancelUrl = hasLiveRevision ? updateReviewUrl : reviewUrl;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">{heading}</h1>
            {isLoadingContext ? (
              <p className="govuk-body-l">Loading...</p>
            ) : (
              <p className="govuk-body-l">
                Please confirm that you would like to {contextAction}
                {datasetName ? ` "${datasetName}"` : ''}. Any changes you have made so far will not be saved.
              </p>
            )}

            {errorMessage && (
              <div className="govuk-error-summary" role="alert" aria-labelledby="avl-delete-error-title">
                <h2 className="govuk-error-summary__title" id="avl-delete-error-title">
                  There is a problem
                </h2>
                <div className="govuk-error-summary__body">
                  <ul className="govuk-list govuk-error-summary__list">
                    <li>{errorMessage}</li>
                  </ul>
                </div>
              </div>
            )}

            <div className="govuk-button-group">
              <button type="button" className="govuk-button" onClick={handleDelete} disabled={isSubmitting}>
                {isSubmitting ? 'Deleting...' : 'Delete'}
              </button>
              <Link className="govuk-button govuk-button--secondary" href={cancelUrl}>
                Cancel
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function AvlDeletePage() {
  return (
    <ProtectedRoute>
      <AvlDeletePageContent />
    </ProtectedRoute>
  );
}
