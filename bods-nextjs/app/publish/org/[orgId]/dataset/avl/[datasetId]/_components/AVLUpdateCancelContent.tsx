'use client';

import Link from 'next/link';
import { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { api } from '@/lib/api-client';

const DRAFT_LIKE_STATUSES = new Set(['draft', 'success', 'indexing', 'pending', 'processing']);

export function AVLUpdateCancelContent() {
  const params = useParams();
  const router = useRouter();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const formUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update`;
  const detailUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}`;
  const reviewUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/review`;
  const [confirmUrl, setConfirmUrl] = useState(detailUrl);

  useEffect(() => {
    let isCancelled = false;

    const resolveConfirmUrl = async () => {
      try {
        const detail = await api.get<{ status?: string }>(`/api/publish/avl/detail/${orgId}/${datasetId}/`);

        if (!isCancelled) {
          setConfirmUrl(DRAFT_LIKE_STATUSES.has(detail.status ?? '') ? reviewUrl : detailUrl);
        }
      } catch {
        if (!isCancelled) {
          setConfirmUrl(detailUrl);
        }
      }
    };

    resolveConfirmUrl();

    return () => {
      isCancelled = true;
    };
  }, [datasetId, detailUrl, orgId, reviewUrl]);

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
            <h1 className="govuk-heading-xl">Would you like to cancel updating this data feed?</h1>
            <p className="govuk-body">Any changes you have made so far will not be saved.</p>

            <div className="govuk-button-group">
              <Link role="button" className="govuk-button" href={confirmUrl}>
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
