'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { PublishStepper } from '@/components/publish';
import { api } from '@/lib/api-client';
import { config } from '@/config';
import { formatDateTime } from '@/lib/utils/date';
import { validateAvlConsentStep } from '@/lib/validation/avl-publish';
import { AvlReviewErrorGuidance, AvlReviewHelpAside } from './AvlReviewAuxiliaryPanels';
import { statusIndicatorClass, statusLabel } from './avlStatus';

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
  isUpdate: boolean;
};

const POLL_INTERVAL_MS = 1000;

export function AvlReviewPageContent({ isUpdate }: AvlReviewPageContentProps) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [statusData, setStatusData] = useState<AvlReviewStatusResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [errorMessage, setErrorMessage] = useState('');

  const updateUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update`;
  const deleteUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/delete`;
  const djangoApiBaseUrl = config.djangoApiBaseUrl;
  const djangoPublishBaseUrl = djangoApiBaseUrl.replace('://localhost', '://publish.localhost');
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
  const contactSupportUrl = `${djangoApiBaseUrl}/contact/`;

  useEffect(() => {
    let isCancelled = false;

    const fetchStatus = async () => {
      try {
        const data = await api.get<AvlReviewStatusResponse>(`/api/avl/review-status/${orgId}/${datasetId}/`);

        if (!isCancelled) {
          setStatusData(data);
          setErrorMessage('');
          setIsInitialLoading(false);
        }

        if (!data.loading) {
          clearInterval(intervalId);
        }
      } catch {
        if (!isCancelled) {
          setErrorMessage('Unable to check processing status. Please refresh and try again.');
          setIsInitialLoading(false);
        }
      }
    };

    const intervalId = setInterval(fetchStatus, POLL_INTERVAL_MS);
    fetchStatus();

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

    const validationErrors = validateAvlConsentStep(hasReviewed);
    setErrors(validationErrors);
    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const publishPath = `/api/avl/publish/${orgId}/${datasetId}/`;
      const data = await api.post<{ error?: string; redirect?: string }>(
        publishPath,
      );

      globalThis.location.href = data.redirect || (isUpdate
        ? `/publish/org/${orgId}/dataset/avl/${datasetId}/update/success`
        : `/publish/org/${orgId}/dataset/avl/${datasetId}/success`);
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'An error occurred while publishing. Please try again.');
      setIsPublishing(false);
    }
  };

  const loading = statusData?.loading ?? true;
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? 0));
  const reviewErrorMessage = statusData?.error || '';

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
              There is a problem
            </h2>
            <div className="govuk-error-summary__body">
              <ul className="govuk-list govuk-error-summary__list">
                <li className="no-underline-l app-error-summary__item">{errorMessage}</li>
              </ul>
            </div>
          </div>
        )}

        <h1 className="govuk-heading-l">Review and publish</h1>
        <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">

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
                {!reviewErrorMessage && (
                  <div className="govuk-!-margin-bottom-6">
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
                    <button
                      type="button"
                      className="govuk-button"
                      disabled={!hasReviewed || isPublishing}
                      onClick={handlePublish}
                    >
                      {isPublishing ? 'Publishing...' : 'Publish data feed'}
                    </button>
                  </div>
                )}

                {reviewErrorMessage && (
                  <>
                    <div
                      className="govuk-error-summary govuk-!-margin-bottom-0"
                      aria-labelledby="avl-review-error-title"
                      role="alert"
                      tabIndex={-1}
                      data-module="govuk-error-summary"
                    >
                      <h2 className="govuk-error-summary__title govuk-!-margin-bottom-2" id="avl-review-error-title">
                        Supplied data feed has failed to upload
                      </h2>
                      <div className="govuk-error-summary__body">
                        <ul className="govuk-list govuk-error-summary__list">
                          <li className="no-underline-l app-error-summary__item">{reviewErrorMessage}</li>
                        </ul>
                      </div>
                    </div>

                    <div className="govuk-!-padding-bottom-7 govuk-!-padding-top-5">
                      <Link role="button" className="govuk-button govuk-!-margin-bottom-0" href={updateUrl}>
                        Publish correct data feed
                      </Link>
                    </div>
                  </>
                )}

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
                      <th scope="row" className="govuk-table__header">Description</th>
                      <td className="govuk-table__cell">{statusData?.description || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Short description</th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.shortDescription || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Status</th>
                      <td className="govuk-table__cell">
                        <span className={`status-indicator ${statusIndicatorClass(statusData?.status)}`}>
                          {statusLabel(statusData?.status)}
                        </span>
                      </td>
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
                      <th scope="row" className="govuk-table__header">URL link</th>
                      <td className="govuk-table__cell">
                        <span className="dont-break-out" style={{ display: 'block', maxWidth: '100%', overflowWrap: 'anywhere' }}>
                          {statusData?.urlLink || '-'}
                        </span>
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Feed details last updated</th>
                      <td className="govuk-table__cell">
                        {statusData?.lastModified
                          ? `${formatDateTime(statusData.lastModified)}${statusData.lastModifiedUser ? ` by ${statusData.lastModifiedUser}` : ''}`
                          : '-'}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Last automated update</th>
                      <td className="govuk-table__cell">Unknown</td>
                    </tr>
                  </tbody>
                </table>

                {reviewErrorMessage && (
                  <AvlReviewErrorGuidance deleteUrl={deleteUrl} />
                )}

                {!reviewErrorMessage && (
                  <div className="btn-group-justified govuk-button-group">
                    <Link role="button" className="govuk-button govuk-button--secondary" href={deleteUrl}>
                      Delete data feed
                    </Link>
                    <Link role="button" className="govuk-button govuk-button--secondary" href={updateUrl}>
                      Publish correct data feed
                    </Link>
                  </div>
                )}
              </div>
            )}
          </div>
          <AvlReviewHelpAside
            supportBusOperatorsUrl={supportBusOperatorsUrl}
            contactSupportUrl={contactSupportUrl}
          />
        </div>
      </div>
    </div>
  );
}
