'use client';

import Link from 'next/link';
import { useEffect, useMemo, useState } from 'react';
import { useParams } from 'next/navigation';
import { PublishStepper } from '@/components/publish';
import { formatDateTime } from '@/lib/utils/date';
import { validateAvlConsentStep } from '@/lib/validation/avl-publish';

type AvlReviewStatusResponse = {
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
  siriVersion?: string;
  lastModified?: string;
  lastModifiedUser?: string;
  error?: string | null;
};

type AvlReviewPageContentProps = {
  reviewStatusPath: string;
  publishPath: string;
  isUpdate: boolean;
};

const POLL_INTERVAL_MS = 1000;

export function AvlReviewPageContent({ reviewStatusPath, publishPath, isUpdate }: AvlReviewPageContentProps) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [statusData, setStatusData] = useState<AvlReviewStatusResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [errorMessage, setErrorMessage] = useState('');

  const listUrl = `/publish/org/${orgId}/dataset/avl`;
  const updateUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update`;
  const deleteUrl = listUrl;

  const token = useMemo(() => {
    if (!globalThis.window) {
      return null;
    }

    return globalThis.window.localStorage.getItem('bods.auth.access');
  }, []);

  useEffect(() => {
    let isCancelled = false;
    let intervalId: ReturnType<typeof setInterval> | undefined;

    const fetchStatus = async () => {
      if (!token) {
        if (!isCancelled) {
          setErrorMessage('Not authenticated. Please sign in and retry.');
          setIsInitialLoading(false);
        }
        return;
      }

      try {
        const response = await fetch(`${reviewStatusPath}?orgId=${orgId}&datasetId=${datasetId}`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = (await response.json().catch(() => ({}))) as AvlReviewStatusResponse & {
          error?: string;
        };

        if (!response.ok) {
          if (!isCancelled) {
            setErrorMessage(data.error || `Status check failed (${response.status}).`);
            setIsInitialLoading(false);
          }
          return;
        }

        if (!isCancelled) {
          setStatusData(data);
          setErrorMessage('');
          setIsInitialLoading(false);
        }

        if (!data.loading && intervalId) {
          clearInterval(intervalId);
        }
      } catch {
        if (!isCancelled) {
          setErrorMessage('Unable to check processing status. Please refresh and try again.');
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
  }, [datasetId, orgId, reviewStatusPath, token]);

  const handlePublish = async () => {
    if (!token || isPublishing) {
      return;
    }

    const validationErrors = validateAvlConsentStep(hasReviewed);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const response = await fetch(
        `${publishPath}?orgId=${orgId}&datasetId=${datasetId}&isUpdate=${isUpdate}`,
        {
          method: 'POST',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        },
      );

      const data = (await response.json().catch(() => ({}))) as { error?: string; redirect?: string };

      if (!response.ok) {
        setErrorMessage(data.error || `Publish failed (${response.status}).`);
        setIsPublishing(false);
        return;
      }

      globalThis.location.href = data.redirect || (isUpdate
        ? `/publish/org/${orgId}/dataset/avl/${datasetId}/update/success`
        : `/publish/org/${orgId}/dataset/avl/${datasetId}/success`);
    } catch {
      setErrorMessage('An error occurred while publishing. Please try again.');
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
              { label: isUpdate ? '1. Add update comment' : '1. Describe your data feed', state: 'previous' },
              { label: '2. Provide your data', state: 'previous' },
              { label: '3. Review and publish', state: 'selected' },
            ]}
          />
        </div>

        {errorMessage && (
          <div
            className="govuk-error-summary govuk-!-margin-bottom-0"
            aria-labelledby="error-summary-title"
            role="alert"
            tabIndex={-1}
            data-module="govuk-error-summary"
          >
            <h2 className="govuk-error-summary__title govuk-!-margin-bottom-2" id="error-summary-title">
              Supplied data feed has failed to upload
            </h2>
            <div className="govuk-error-summary__body">
              <ul className="govuk-list govuk-error-summary__list">
                <li className="no-underline-l app-error-summary__item">{errorMessage}</li>
              </ul>
            </div>
          </div>
        )}

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">Review and publish</h1>

            {isInitialLoading || loading ? (
              <div className="govuk-panel blue-background govuk-panel--confirmation">
                <h2 className="govuk-panel__title govuk-!-font-size-36">Your data is being processed</h2>
                <div className="govuk-panel__body govuk-!-font-size-19">
                  <div className="pb3-l">
                    Once successfully processed, the feed will be published,
                    <br />
                    and you will be able to view the details here
                  </div>
                  <div id="progressOuterDiv" className="progress-bar-outer">
                    <div id="progressInnerDiv" className="progress-bar-inner" style={{ width: `${progress}%` }} />
                  </div>
                  <span id="progressSpan" className="progress-bar-text">
                    {progress}%
                  </span>
                </div>
              </div>
            ) : (
              <div id="preview-section">
                <h2 className="govuk-heading-l dont-break-out">{statusData?.name || 'AVL data feed'}</h2>

                <table className="govuk-table dataset-property-table">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Name</th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.name || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Data feed ID</th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.datasetId || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">URL link</th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.urlLink || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Description</th>
                      <td className="govuk-table__cell">{statusData?.description || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Short description</th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.shortDescription || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Status</th>
                      <td className="govuk-table__cell">{statusData?.status || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Owner</th>
                      <td className="govuk-table__cell">{statusData?.ownerName || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">SIRI-VM version</th>
                      <td className="govuk-table__cell">{statusData?.siriVersion || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Last modified</th>
                      <td className="govuk-table__cell">{formatDateTime(statusData?.lastModified)}</td>
                    </tr>
                  </tbody>
                </table>

                <div className="govuk-form-group">
                  <div className="govuk-checkboxes__item">
                    <input
                      className="govuk-checkboxes__input"
                      id="id_has_reviewed"
                      type="checkbox"
                      checked={hasReviewed}
                      onChange={(event) => {
                        setHasReviewed(event.target.checked);
                        setErrors({});
                      }}
                    />
                    <label className="govuk-label govuk-checkboxes__label" htmlFor="id_has_reviewed">
                      I have reviewed the data and wish to publish my data
                    </label>
                  </div>
                  {errors.consent && <p className="govuk-error-message">{errors.consent}</p>}
                </div>

                <div className="btn-group-justified govuk-button-group">
                  <button
                    type="button"
                    className="govuk-button"
                    disabled={isPublishing}
                    onClick={handlePublish}
                  >
                    {isPublishing ? 'Publishing...' : 'Publish data feed'}
                  </button>
                  <Link role="button" className="govuk-button govuk-button--secondary" href={deleteUrl}>
                    Delete data feed
                  </Link>
                  <Link role="button" className="govuk-button govuk-button--secondary" href={updateUrl}>
                    Publish correct data feed
                  </Link>
                  <Link className="govuk-link" href={listUrl}>
                    Back to data feeds
                  </Link>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
