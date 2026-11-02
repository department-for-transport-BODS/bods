'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ErrorSummary } from '@/components/shared';
import { api, getCsrfToken } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';

export function AvlArchivePageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [datasetName, setDatasetName] = useState('');

  const detailUrl = publishAppPath(`/org/${orgId}/dataset/avl/${datasetId}/`);
  const fallbackSuccessUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/deactivate/success`;

  // Django's success page shows the feed name; it is read now because the feed
  // is no longer published once deactivated.
  useEffect(() => {
    let cancelled = false;
    api
      .get<{ name?: string }>(`/api/publish/avl/detail/${orgId}/${datasetId}/`)
      .then((detail) => {
        if (!cancelled) {
          setDatasetName(detail.name || '');
        }
      })
      .catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [datasetId, orgId]);

  const handleDeactivate = async () => {
    if (isSubmitting) {
      return;
    }

    setIsSubmitting(true);
    setErrorMessage('');

    try {
      const csrfToken = getCsrfToken();
      const response = await fetch(`/api/next/avl/archive?orgId=${orgId}&datasetId=${datasetId}`, {
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

        <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="avl-archive-error-title" />

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
