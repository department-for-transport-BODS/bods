'use client';

import Link from 'next/link';
import { useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { PublishStepper } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { HOSTS } from '@/config';
import { formatDateTime } from '@/lib/utils/date';
import { validateAvlConsentStep } from '@/lib/validation/avl-publish';
import { useDatasetReview } from '@/hooks/useDatasetReview';
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

export function AvlReviewPageContent({ isUpdate }: AvlReviewPageContentProps) {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const refreshToken = searchParams.get('refresh') || '';

  const {
    statusData,
    processingProgress,
    isInitialLoading,
    errorMessage,
    setErrorMessage,
  } = useDatasetReview<AvlReviewStatusResponse>(
    datasetId,
    `/api/publish/avl/review-status/${orgId}/${datasetId}/`,
    'Unable to check processing status. Please refresh and try again.',
    refreshToken,
  );
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const updateUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/update`;
  const deleteUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/delete`;
  const reviewUrl = isUpdate
    ? `/publish/org/${orgId}/dataset/avl/${datasetId}/update/review`
    : `/publish/org/${orgId}/dataset/avl/${datasetId}/review`;
  const editUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/dataset-edit?mode=revision&redirect=${encodeURIComponent(reviewUrl)}`;
  const supportBusOperatorsUrl = `${HOSTS.publish}/guidance/operator-requirements/`;
  const contactSupportUrl = `${HOSTS.www}/contact/`;

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
      const publishPath = `/api/publish/avl/publish/${orgId}/${datasetId}/`;
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
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? processingProgress));
  const reviewErrorMessage = statusData?.error || '';

  return (
    <div className="govuk-width-container">
      <div className="govuk-breadcrumbs">
        <PublishStepper
          steps={[
            { label: isUpdate ? '1. Comment' : '1. Describe data', state: 'previous' },
            { label: isUpdate ? '2. Update' : '2. Provide data', state: 'previous' },
            { label: '3. Review and publish', state: 'selected' },
          ]}
        />
      </div>

      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl dont-break-out govuk-!-padding-top-3 govuk-!-padding-bottom-3 govuk-!-margin-bottom-4">
              Review and publish
            </h1>
          </div>
        </div>

        <ErrorSummary
          errors={errorMessage ? [errorMessage] : []}
          className="govuk-!-margin-bottom-0"
          titleClassName="govuk-!-margin-bottom-2"
          itemClassName="no-underline-l app-error-summary__item"
          tabIndex={-1}
          dataModule="govuk-error-summary"
        />

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
                      <div className="govuk-checkboxes govuk-checkboxes--small">
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
                      </div>
                      {errors.consent && <p className="govuk-error-message">{errors.consent}</p>}
                    </div>
                    <button
                      type="button"
                      className="govuk-button"
                      disabled={!hasReviewed || isPublishing}
                      onClick={handlePublish}
                    >
                      {isPublishing ? 'Publishing...' : 'Publish data'}
                    </button>
                  </div>
                )}

                {reviewErrorMessage && (
                  <>
                    <ErrorSummary
                      errors={[reviewErrorMessage]}
                      title="Supplied data feed has failed to upload"
                      className="govuk-!-margin-bottom-0"
                      titleClassName="govuk-!-margin-bottom-2"
                      itemClassName="no-underline-l app-error-summary__item"
                      tabIndex={-1}
                      dataModule="govuk-error-summary"
                    />

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
                      <td className="govuk-table__cell">
                        <div className="flex-between">
                          <span className="dont-break-out">{statusData?.description || '-'}</span>
                          <Link className="govuk-link" href={editUrl}>
                            Edit
                          </Link>
                        </div>
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Short description</th>
                      <td className="govuk-table__cell dont-break-out">
                        <div className="flex-between">
                          <span>{statusData?.shortDescription || '-'}</span>
                          <Link className="govuk-link" href={editUrl}>
                            Edit
                          </Link>
                        </div>
                      </td>
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
                    {!reviewErrorMessage && (
                      <>
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
                      </>
                    )}
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
