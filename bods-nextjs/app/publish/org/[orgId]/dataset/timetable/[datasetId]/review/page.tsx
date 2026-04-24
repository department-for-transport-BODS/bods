'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';
import { PublishStepper } from '@/components/publish';
import { formatDateTime } from '@/lib/utils/date';

type TimetableMetadata = {
  filename?: string;
  serviceCode?: string;
  nationalOperatorCode?: string;
  lineNames?: string;
  origin?: string;
  destination?: string;
  operatingPeriodStartDate?: string | null;
  operatingPeriodEndDate?: string | null;
  schemaVersion?: string;
  revisionNumber?: string;
  modification?: string;
  serviceMode?: string;
};

type TimetableReviewStatusResponse = {
  datasetId: number;
  revisionId: number;
  status: string;
  progress: number;
  loading: boolean;
  name?: string;
  description?: string;
  shortDescription?: string;
  urlLink?: string;
  ownerName?: string;
  downloadUrl?: string;
  lastModified?: string;
  lastModifiedUser?: string;
  metadata?: TimetableMetadata[];
  error?: string | null;
};

type PublishResponse = {
  redirect?: string;
  published?: boolean;
};

const POLL_INTERVAL_MS = 1000;

function TimetableReviewPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const timetablesListUrl = `/publish/org/${orgId}/dataset/timetable`;

  const [statusData, setStatusData] = useState<TimetableReviewStatusResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isCancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const fetchStatus = async () => {
      try {
        const data = await api.get<TimetableReviewStatusResponse>(
          `/api/timetables/review-status/${orgId}/${datasetId}/`,
        );

        if (!isCancelled) {
          setStatusData(data);
          setErrorMessage('');
          setIsInitialLoading(false);
        }

        if (!data.loading && intervalId) {
          clearInterval(intervalId);
        }
      } catch (error) {
        if (!isCancelled) {
          const message = error instanceof Error ? error.message : 'Unable to check processing status.';
          setErrorMessage(message);
          setIsInitialLoading(false);
        }
      }
    };

    fetchStatus();
    intervalId = setInterval(fetchStatus, POLL_INTERVAL_MS);

    return () => {
      isCancelled = true;
      if (intervalId) {
        clearInterval(intervalId);
      }
    };
  }, [datasetId, orgId]);

  const handlePublish = async () => {
    if (isPublishing) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const data = await api.post<PublishResponse>(`/api/timetables/publish/${orgId}/${datasetId}/`);
      globalThis.location.href = data.redirect || timetablesListUrl;
    } catch (error) {
      const message = error instanceof Error ? error.message : 'An error occurred while publishing.';
      setErrorMessage(message);
      setIsPublishing(false);
    }
  };

  const loading = statusData?.loading ?? true;
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? 0));

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <PublishStepper
            steps={[
              { label: '1. Describe data', state: 'previous' },
              { label: '2. Provide data', state: 'previous' },
              { label: '3. Review and publish', state: 'selected' },
            ]}
          />
        </div>

        {errorMessage ? (
          <div className="govuk-error-summary" role="alert" aria-labelledby="timetable-review-error-title">
            <h2 className="govuk-error-summary__title" id="timetable-review-error-title">
              There is a problem
            </h2>
            <div className="govuk-error-summary__body">
              <ul className="govuk-list govuk-error-summary__list">
                <li>{errorMessage}</li>
              </ul>
            </div>
          </div>
        ) : null}

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">Review and publish</h1>

            {isInitialLoading || loading ? (
              <div className="govuk-panel govuk-panel--confirmation bods-bg-blue-light">
                <h2 className="govuk-panel__title govuk-!-font-size-36">Your data is being processed</h2>
                <div className="govuk-panel__body">{progress}%</div>
              </div>
            ) : (
              <>
                <dl className="govuk-summary-list">
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Status</dt>
                    <dd className="govuk-summary-list__value">{statusData?.status || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Data set description</dt>
                    <dd className="govuk-summary-list__value">{statusData?.description || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Short description</dt>
                    <dd className="govuk-summary-list__value">{statusData?.shortDescription || '-'}</dd>
                  </div>
                  <div className="govuk-summary-list__row">
                    <dt className="govuk-summary-list__key">Last modified</dt>
                    <dd className="govuk-summary-list__value">{formatDateTime(statusData?.lastModified)}</dd>
                  </div>
                </dl>

                {statusData?.metadata && statusData.metadata.length > 0 ? (
                  <>
                    <h2 className="govuk-heading-m">Detected services</h2>
                    <table className="govuk-table">
                      <thead className="govuk-table__head">
                        <tr className="govuk-table__row">
                          <th className="govuk-table__header">Filename</th>
                          <th className="govuk-table__header">Service code</th>
                          <th className="govuk-table__header">Line names</th>
                        </tr>
                      </thead>
                      <tbody className="govuk-table__body">
                        {statusData.metadata.map((item, index) => (
                          <tr key={`${item.filename || 'file'}-${index}`} className="govuk-table__row">
                            <td className="govuk-table__cell">{item.filename || '-'}</td>
                            <td className="govuk-table__cell">{item.serviceCode || '-'}</td>
                            <td className="govuk-table__cell">{item.lineNames || '-'}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </>
                ) : null}

                <div className="govuk-form-group">
                  <div className="govuk-checkboxes__item">
                    <input
                      className="govuk-checkboxes__input"
                      id="id_has_reviewed"
                      type="checkbox"
                      checked={hasReviewed}
                      onChange={(event) => setHasReviewed(event.target.checked)}
                    />
                    <label className="govuk-label govuk-checkboxes__label" htmlFor="id_has_reviewed">
                      I have reviewed the data quality report and wish to publish my data
                    </label>
                  </div>
                </div>

                <div className="govuk-button-group">
                  <button
                    type="button"
                    className="govuk-button"
                    disabled={!hasReviewed || isPublishing || loading}
                    onClick={handlePublish}
                  >
                    {isPublishing ? 'Publishing...' : 'Publish'}
                  </button>
                  <Link className="govuk-link" href={timetablesListUrl}>
                    Back to data sets
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TimetableReviewPage() {
  return (
    <ProtectedRoute>
      <TimetableReviewPageContent />
    </ProtectedRoute>
  );
}