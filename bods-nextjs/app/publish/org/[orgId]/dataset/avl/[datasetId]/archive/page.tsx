'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { getCsrfToken } from '@/lib/api-client';

function AvlArchivePageContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  const datasetName = searchParams.get('name') || '';
  const detailUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}`;
  const fallbackSuccessUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/archive/success`;

  const handleDeactivate = async () => {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(`/api/avl/archive?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        credentials: 'include',
        headers: csrfToken ? { 'X-CSRFToken': csrfToken } : {},
      });

      const data = (await response.json().catch(() => ({}))) as {
        redirect?: string;
        error?: string;
      };

      if (!response.ok) {
        throw new Error(data.error || 'Unable to deactivate data feed. Please try again.');
      }

      const successUrl = data.redirect || fallbackSuccessUrl;
      if (datasetName) {
        const url = new URL(successUrl, globalThis.location.origin);
        if (!url.searchParams.has('name')) {
          url.searchParams.set('name', datasetName);
        }
        globalThis.location.href = `${url.pathname}${url.search}`;
        return;
      }

      globalThis.location.href = successUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to deactivate data feed. Please try again.');
      setIsSubmitting(false);
    }
  };

  return (
    <div className="govuk-width-container">
        <Link className="govuk-back-link" href={detailUrl}>
          Back
        </Link>
        <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-three-quarters">
            <h1 className="govuk-heading-xl">Would you like to deactivate this data feed?</h1>
          </div>
        </div>

        {errorMessage && (
          <div className="govuk-error-summary" role="alert" aria-labelledby="avl-archive-error-title">
            <h2 className="govuk-error-summary__title" id="avl-archive-error-title">
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
          <button type="button" className="govuk-button" onClick={handleDeactivate} disabled={isSubmitting}>
            {isSubmitting ? 'Confirming...' : 'Confirm'}
          </button>
          <Link className="govuk-button govuk-button--secondary" href={detailUrl}>
            Cancel
          </Link>
        </div>
      </div>
    </div>
  );
}

export default function AvlArchivePage() {
  return (
    <ProtectedRoute>
      <AvlArchivePageContent />
    </ProtectedRoute>
  );
}
