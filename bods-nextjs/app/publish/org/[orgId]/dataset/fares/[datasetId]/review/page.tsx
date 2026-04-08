// This file implements the "Review and publish" page for a fares dataset in the BODS Next.js frontend
// It fetches the processing status of the uploaded dataset from a custom API route, 
// displays relevant information and metadata about the dataset, 
// and allows the user to publish it once they have reviewed the details. The page also includes error handling and links to support resources.
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

type ReviewStatusResponse = {
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
  schemaVersion?: string;
  downloadUrl?: string;
  lastModified?: string;
  lastModifiedUser?: string;
  metadata?: {
    numOfFareZones?: number | null;
    numOfLines?: number | null;
    numOfSalesOfferPackages?: number | null;
    numOfFareProducts?: number | null;
    numOfUserProfiles?: number | null;
    validFrom?: string | null;
    validTo?: string | null;
  };
  error?: string | null;
};

const POLL_INTERVAL_MS = 1000;

function FaresReviewPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const djangoApiBaseUrl = process.env.NEXT_PUBLIC_DJANGO_API_URL || 'http://localhost:8000';
  const djangoPublishBaseUrl =
    process.env.NEXT_PUBLIC_DJANGO_PUBLISH_URL || djangoApiBaseUrl.replace('://localhost', '://publish.localhost');

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const createFaresUrl = `/publish/org/${orgId}/dataset/fares/create`;
  const supportBusOperatorsUrl = `${djangoPublishBaseUrl}/guidance/operator-requirements/`;
  const contactSupportUrl = `${djangoApiBaseUrl}/contact/`;

  const [statusData, setStatusData] = useState<ReviewStatusResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

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
        const resp = await fetch(`/api/fares/review-status?orgId=${orgId}&datasetId=${datasetId}`, {
          method: 'GET',
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const data = (await resp.json().catch(() => ({}))) as ReviewStatusResponse & {
          error?: string;
        };

        if (!resp.ok) {
          if (!isCancelled) {
            setErrorMessage(data.error || `Status check failed (${resp.status}).`);
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
  }, [datasetId, orgId, token]);

  const handlePublish = async () => {
    if (!token || isPublishing) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const resp = await fetch(`/api/fares/publish?orgId=${orgId}&datasetId=${datasetId}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      const data = (await resp.json().catch(() => ({}))) as {
        error?: string;
        redirect?: string;
      };

      if (!resp.ok) {
        setErrorMessage(data.error || `Publish failed (${resp.status}).`);
        setIsPublishing(false);
        return;
      }

      globalThis.location.href = data.redirect || faresListUrl;
    } catch {
      setErrorMessage('An error occurred while publishing. Please try again.');
      setIsPublishing(false);
    }
  };

  const loading = statusData?.loading ?? true;
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? 0));

  const formatDateTime = (value?: string | null) => {
    if (!value) {
      return '-';
    }

    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
      return '-';
    }

    return new Intl.DateTimeFormat('en-GB', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      hour12: false,
    }).format(date);
  };

  const statusIndicatorClass = (status?: string) => {
    if (!status) {
      return 'status-indicator--draft';
    }

    if (status === 'live' || status === 'published') {
      return 'status-indicator--success';
    }

    if (status === 'error') {
      return 'status-indicator--error';
    }

    if (status === 'warning') {
      return 'status-indicator--warning';
    }

    if (status === 'indexing' || status === 'pending' || status === 'processing') {
      return 'status-indicator--indexing';
    }

    return 'status-indicator--draft';
  };

  const statusLabel = (status?: string) => {
    if (!status) {
      return 'Draft';
    }

    if (status === 'live' || status === 'published') {
      return 'Published';
    }

    if (status === 'indexing' || status === 'pending' || status === 'processing') {
      return 'Processing';
    }

    if (status === 'success' || status === 'draft') {
      return 'Draft';
    }

    return status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-breadcrumbs">
          <ol className="publish-stepper govuk-breadcrumbs__list" aria-label="Progress">
            <li className="publish-stepper__item publish-stepper__item--previous">1. Describe data</li>
            <li className="publish-stepper__item publish-stepper__item--previous">2. Provide data</li>
            <li className="publish-stepper__item publish-stepper__item--selected">3. Review and publish</li>
          </ol>
        </div>

        {errorMessage ? (
          <div className="govuk-error-summary" role="alert" aria-labelledby="fares-review-error-title">
            <h2 className="govuk-error-summary__title" id="fares-review-error-title">
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
                <div className="govuk-panel__body govuk-!-font-size-19">
                  <div className="pb3-l">
                    The data format is being checked to confirm it is NeTEx.
                    <br />
                    Once successfully validated the data set details will
                    <br />
                    be shown here.
                  </div>
                  <div id="progressOuterDiv" className="progress-bar-outer">
                    <div
                      className="loading-white"
                      id="progressInnerDiv"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <span className="loading-white-lg" id="progressSpan">
                    {progress}%
                  </span>
                </div>
              </div>
            ) : (
              <>
                <div className="app-dqs-panel govuk-!-margin-bottom-7">
                  <div className="app-dqs-panel__body">
                    <div className="app-dqs-panel__success">
                      <h2 className="govuk-heading-m govuk-!-margin-bottom-0">
                        {statusData?.error ? 'Validation Check - Failed' : 'Validation Check - Passed'}
                      </h2>
                    </div>
                  </div>
                </div>

                <div className="govuk-!-margin-bottom-6">
                  <div className="govuk-checkboxes" data-module="govuk-checkboxes">
                    <div className="govuk-checkboxes__item">
                      <input
                        className="govuk-checkboxes__input"
                        id="publish-review-confirmation"
                        name="publish-review-confirmation"
                        type="checkbox"
                        checked={hasReviewed}
                        onChange={(event) => setHasReviewed(event.target.checked)}
                      />
                      <label className="govuk-label govuk-checkboxes__label" htmlFor="publish-review-confirmation">
                        I have reviewed the submission and wish to publish my data
                      </label>
                    </div>
                  </div>

                  <button
                    type="button"
                    className="govuk-button"
                    onClick={handlePublish}
                    disabled={isPublishing || !hasReviewed}
                    aria-disabled={isPublishing || !hasReviewed}
                  >
                    {isPublishing ? 'Publishing...' : 'Publish data'}
                  </button>
                </div>

                <h2 className="govuk-heading-l dont-break-out">{statusData?.name || 'Unnamed fares dataset'}</h2>

                <div className="review-map-placeholder govuk-!-margin-bottom-5" aria-hidden="true">
                  <div className="review-map-placeholder__inner">Map preview</div>
                </div>

                <table className="govuk-table dataset-property-table">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Name
                      </th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.name || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Data set ID
                      </th>
                      <td className="govuk-table__cell dont-break-out">{statusData?.datasetId || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        URL link
                      </th>
                      <td className="govuk-table__cell">
                        {statusData?.urlLink ? (
                          <a className="govuk-link" href={statusData.urlLink}>
                            Publisher URL
                          </a>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Description
                      </th>
                      <td className="govuk-table__cell">{statusData?.description || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Short description
                      </th>
                      <td className="govuk-table__cell">{statusData?.shortDescription || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Status
                      </th>
                      <td className="govuk-table__cell">
                        <span className={`status-indicator ${statusIndicatorClass(statusData?.status)}`}>
                          {statusLabel(statusData?.status)}
                        </span>
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Owner
                      </th>
                      <td className="govuk-table__cell">{statusData?.ownerName || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        NeTEx Version
                      </th>
                      <td className="govuk-table__cell">{statusData?.schemaVersion || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Download NeTEx
                      </th>
                      <td className="govuk-table__cell">
                        {statusData?.downloadUrl ? (
                          <a className="govuk-link" href={statusData.downloadUrl}>
                            Download .xml (NeTEx)
                          </a>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Last updated
                      </th>
                      <td className="govuk-table__cell">
                        {formatDateTime(statusData?.lastModified)}
                        {statusData?.lastModifiedUser ? ` by ${statusData.lastModifiedUser}` : ''}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Number of fare zones
                      </th>
                      <td className="govuk-table__cell">{statusData?.metadata?.numOfFareZones ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Number of lines
                      </th>
                      <td className="govuk-table__cell">{statusData?.metadata?.numOfLines ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Number of sales offer packages
                      </th>
                      <td className="govuk-table__cell">{statusData?.metadata?.numOfSalesOfferPackages ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Number of fare products
                      </th>
                      <td className="govuk-table__cell">{statusData?.metadata?.numOfFareProducts ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Number of user types
                      </th>
                      <td className="govuk-table__cell">{statusData?.metadata?.numOfUserProfiles ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Earliest start date
                      </th>
                      <td className="govuk-table__cell">{formatDateTime(statusData?.metadata?.validFrom)}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">
                        Earliest end date
                      </th>
                      <td className="govuk-table__cell">{formatDateTime(statusData?.metadata?.validTo)}</td>
                    </tr>
                  </tbody>
                </table>

                <div className="govuk-button-group">
                  <Link className="govuk-link" href={faresListUrl}>
                    Back to fares data sets
                  </Link>
                  <Link className="govuk-link" href={createFaresUrl}>
                    Upload another fares data set
                  </Link>
                </div>
              </>
            )}
          </div>

          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link" href={supportBusOperatorsUrl}>
                  View our guidelines here
                </a>
              </li>
              <li>
                <a className="govuk-link" href={contactSupportUrl}>
                  Contact support desk
                </a>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function FaresReviewPage() {
  return (
    <ProtectedRoute>
      <FaresReviewPageContent />
    </ProtectedRoute>
  );
}
