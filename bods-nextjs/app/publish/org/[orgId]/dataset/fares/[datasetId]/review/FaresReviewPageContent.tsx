// This file implements the "Review and publish" page for a fares dataset in the BODS Next.js frontend
// It fetches the processing status of the uploaded dataset, displays metadata, stop map preview,
// and allows the user to publish once they have reviewed the details.
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import type { Map as MapboxMap } from 'mapbox-gl';
import type { StopPoint } from '@/components/data/StopMap';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { PublishStepper } from '@/components/publish';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils/date';
import { useDatasetReview } from '@/hooks/useDatasetReview';

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
  errorDescription?: string | null;
  schemaValidationReportUrl?: string | null;
  hasLiveRevision?: boolean;
};

const PUBLISHED_STATUSES = new Set(['live', 'expiring', 'warning']);

type FareStopsApiResponse = {
  features?: Array<{
    id?: number;
    geometry?: {
      type?: string;
      coordinates?: [number, number];
    };
    properties?: {
      id?: number;
      atco_code?: string;
      common_name?: string;
    };
  }>;
  error?: string;
};

const parseFareStops = (payload: FareStopsApiResponse): StopPoint[] => {
  const features = Array.isArray(payload.features) ? payload.features : [];

  return features
    .map((feature, index) => {
      const coordinates = feature.geometry?.coordinates;
      const hasValidCoordinates =
        Array.isArray(coordinates) &&
        coordinates.length === 2 &&
        Number.isFinite(coordinates[0]) &&
        Number.isFinite(coordinates[1]);

      if (!hasValidCoordinates) {
        return null;
      }

      const fallbackId = index + 1;

      return {
        id: feature.properties?.id ?? feature.id ?? fallbackId,
        atco_code: feature.properties?.atco_code ?? '',
        common_name: feature.properties?.common_name ?? 'Bus stop',
        location: {
          type: 'Point',
          coordinates: [coordinates[0], coordinates[1]],
        },
      };
    })
    .filter((item): item is StopPoint => item !== null);
};

type FaresStopMapPreviewProps = {
  revisionId?: number;
  mapboxToken: string;
};

type ValidationFailurePanelProps = {
  errorCode?: string | null;
  errorDescription?: string | null;
  schemaValidationReportUrl?: string | null;
  contactSupportUrl: string;
  guidanceUrl: string;
  updateUrl: string;
};

function ValidationFailurePanel({
  errorCode,
  errorDescription,
  schemaValidationReportUrl,
  contactSupportUrl,
  guidanceUrl,
  updateUrl,
}: Readonly<ValidationFailurePanelProps>) {
  const isSchemaError = errorCode === 'SCHEMA_ERROR';
  const descriptionParts = errorDescription?.split(/<\/?br\s*\/?>/i) ?? [];

  return (
    <>
      {isSchemaError ? (
        <div className="app-dqs-panel govuk-!-margin-bottom-7">
          <div className="app-dqs-panel__body">
            <div className="app-dqs-panel__success">
              <h2 className="govuk-heading-m">3a Validation Check - Failed</h2>
              <p className="govuk-body">
                The validation report checks for compliance against the NeTEx schema.
                <br />
                <br />
                {schemaValidationReportUrl ? (
                  <a className="govuk-link" href={schemaValidationReportUrl}>
                    Download schema validation report
                  </a>
                ) : null}
                <br />
              </p>
              <p className="govuk-body govuk-!-margin-bottom-0">
                The fares data supplied is non-compliant and cannot be submitted to BODS as per the{' '}
                <a className="govuk-link" href={guidanceUrl}>
                  guidance.
                </a>{' '}
                To pass the validation please address all outstanding issues in the validation report.
              </p>
            </div>
          </div>
        </div>
      ) : (
        <div
          className="govuk-error-summary govuk-!-margin-bottom-0"
          aria-labelledby="error-summary-title"
          role="alert"
          tabIndex={-1}
          data-module="govuk-error-summary"
        >
          <h2
            className="govuk-error-summary__title govuk-!-margin-bottom-2"
            id="error-summary-title"
          >
            Supplied data set has failed to upload
          </h2>
          <div className="govuk-error-summary__body">
            <ul className="govuk-list govuk-error-summary__list">
              <li className="app-error-summary__item dont-break-out no-underline-l">
                {errorCode === 'SUSPICIOUS_FILE' ? (
                  <>
                    Our antivirus scan detected an issue with your dataset. If you believe this to be
                    wrong, please{' '}
                    <Link className="govuk-link" href={contactSupportUrl}>
                      contact support
                    </Link>
                    .
                  </>
                ) : (
                  descriptionParts.map((part, index) => (
                    <span key={`${index}-${part}`}>
                      {index > 0 ? <br /> : null}
                      {part}
                    </span>
                  ))
                )}
              </li>
            </ul>
          </div>
        </div>
      )}

      <div className="govuk-!-padding-bottom-7 govuk-!-padding-top-5">
        <Link className="govuk-button govuk-!-margin-bottom-0" href={updateUrl}>
          Publish correct data set
        </Link>
      </div>
    </>
  );
}

function ValidationFailureNextSteps() {
  return (
    <>
      <h3 className="govuk-heading-m">What should I do next?</h3>
      <p className="govuk-body govuk-!-font-size-19">
        You can re-upload a different data set file again. Please ensure that your provided data
        format is correct and that your data set file contains valid data.
      </p>
      <p className="govuk-body app-!-text-muted govuk-!-font-size-19">
        Accepted file formats include .xml (NeTEx).
      </p>
    </>
  );
}

function FaresStopMapPreview({ revisionId, mapboxToken }: Readonly<FaresStopMapPreviewProps>) {
  const [fareStops, setFareStops] = useState<StopPoint[]>([]);
  const [isMapLoading, setIsMapLoading] = useState(false);
  const [hasLoadedStops, setHasLoadedStops] = useState(false);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<MapboxMap | null>(null);

  const getMapUnavailableMessage = () => {
    if (isMapLoading) {
      return 'Loading map preview...';
    }

    if (mapboxToken) {
      return 'Map preview unavailable';
    }

    return 'Map preview unavailable: Mapbox token is missing';
  };

  useEffect(() => {
    if (!revisionId) {
      return;
    }

    let isCancelled = false;

    const loadFareStops = async () => {
      setIsMapLoading(true);
      setHasLoadedStops(false);
      try {
        const payload = await api.get<FareStopsApiResponse>(
          `/api/publish/app/fare_stops/?revision=${revisionId}`,
        );
        if (!isCancelled) {
          setFareStops(parseFareStops(payload));
          setHasLoadedStops(true);
        }
      } catch {
        if (!isCancelled) {
          setFareStops([]);
          setHasLoadedStops(false);
        }
      } finally {
        if (!isCancelled) {
          setIsMapLoading(false);
        }
      }
    };

    loadFareStops();

    return () => {
      isCancelled = true;
    };
  }, [revisionId]);

  useEffect(() => {
    let isCancelled = false;

    const initMap = async () => {
      if (!mapboxToken || !mapContainerRef.current || !hasLoadedStops) {
        return;
      }

      mapRef.current?.remove?.();
      mapRef.current = null;

      const mapboxglModule = await import('mapbox-gl');
      const mapboxgl = mapboxglModule.default;

      if (isCancelled || !mapContainerRef.current) {
        return;
      }

      mapboxgl.accessToken = mapboxToken;

      const map = new mapboxgl.Map({
        container: mapContainerRef.current,
        style: 'mapbox://styles/mapbox/light-v9',
        center: [-1.1743, 52.3555],
        zoom: 5,
        maxZoom: 12,
      });

      map.addControl(new mapboxgl.NavigationControl({ showCompass: false }));

      const stopFeatures = fareStops.map((stop) => ({
        type: 'Feature' as const,
        geometry: stop.location,
        properties: {
          atco_code: stop.atco_code,
          common_name: stop.common_name,
        },
      }));

      map.on('load', () => {
        const geojson = {
          type: 'FeatureCollection' as const,
          features: stopFeatures,
        };

        map.addSource('stop-points', {
          type: 'geojson',
          data: geojson,
        });

        map.addLayer({
          id: 'stop-points',
          type: 'circle',
          source: 'stop-points',
          paint: {
            'circle-color': '#49A39A',
            'circle-radius': 5,
          },
        });

        const bounds = new mapboxgl.LngLatBounds();
        for (const stop of fareStops) {
          bounds.extend(stop.location.coordinates);
        }
        if (!bounds.isEmpty()) {
          map.fitBounds(bounds, { padding: 20 });
        }
      });

      mapRef.current = map;
    };

    initMap();

    return () => {
      isCancelled = true;
      mapRef.current?.remove?.();
      mapRef.current = null;
    };
  }, [fareStops, hasLoadedStops, mapboxToken]);

  if (mapboxToken && hasLoadedStops) {
    return (
      <section aria-label="Map preview of fare stop points">
        <div
          ref={mapContainerRef}
          id="map"
          className="disruptions-width govuk-!-margin-bottom-5"
        />
        <style jsx>{`
          .disruptions-width {
            width: 100% !important;
            height: 25rem !important;
          }

          :global(.mapboxgl-popup-content) {
            padding: 12px;
            background: #fff;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
          }
        `}</style>
      </section>
    );
  }

  return (
    <div className="review-map-placeholder govuk-!-margin-bottom-5" aria-hidden="true">
      <div className="review-map-placeholder__inner">{getMapUnavailableMessage()}</div>
    </div>
  );
}

function FaresReviewPageContent({ mapboxToken }: { mapboxToken: string }) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const modifyDraftUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/update?modifyDraft=true`;
  const supportBusOperatorsUrl = '/publish/guide-me';
  const dataQualityGuidanceUrl = `${supportBusOperatorsUrl}?section=dataquality`;
  const contactSupportUrl = '/publish/account';

  const {
    statusData,
    processingProgress,
    isInitialLoading,
    errorMessage,
    setErrorMessage,
  } = useDatasetReview<ReviewStatusResponse>(
    datasetId,
    `/api/publish/fares/review-status/${orgId}/${datasetId}/`,
  );
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const loading = statusData?.loading ?? true;
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? processingProgress));
  const hasBlockingError = Boolean(statusData?.error) || statusData?.status === 'error';
  const canPublish = !hasBlockingError;
  const isUpdate = statusData?.hasLiveRevision ?? false;

  const handlePublish = async () => {
    if (isPublishing) {
      return;
    }

    setIsPublishing(true);
    setErrorMessage('');

    try {
      const data = await api.post<{
        redirect?: string;
      }>(`/api/publish/fares/publish/${orgId}/${datasetId}/`);

      globalThis.location.href = data.redirect || faresListUrl;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'An error occurred while publishing. Please try again.');
      setIsPublishing(false);
    }
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
          <PublishStepper
            steps={
              isUpdate
                ? [
                    { label: '1. Comment', state: 'previous' },
                    { label: '2. Update', state: 'previous' },
                    { label: '3. Review and publish', state: 'selected' },
                  ]
                : [
                    { label: '1. Describe data', state: 'previous' },
                    { label: '2. Provide data', state: 'previous' },
                    { label: '3. Review and publish', state: 'selected' },
                  ]
            }
          />
        </div>

        <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="fares-review-error-title" />

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-0 dont-break-out govuk-!-padding-top-3 govuk-!-padding-bottom-3">
              Review and publish
            </h1>

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
                {hasBlockingError ? (
                  <ValidationFailurePanel
                    errorCode={statusData?.error}
                    errorDescription={statusData?.errorDescription}
                    schemaValidationReportUrl={statusData?.schemaValidationReportUrl}
                    contactSupportUrl={contactSupportUrl}
                    guidanceUrl={dataQualityGuidanceUrl}
                    updateUrl={modifyDraftUrl}
                  />
                ) : null}

                {canPublish ? (
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
                ) : null}

                <h2 className="govuk-heading-l dont-break-out">{statusData?.name || 'Unnamed fares dataset'}</h2>

                <FaresStopMapPreview
                  revisionId={isInitialLoading || loading ? undefined : statusData?.revisionId}
                  mapboxToken={mapboxToken}
                />

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

                {hasBlockingError ? <ValidationFailureNextSteps /> : null}

                <div className="govuk-button-group">
                  {PUBLISHED_STATUSES.has(statusData?.status ?? '') ? null : (
                    <Link
                      className="govuk-button govuk-button--secondary"
                      href={`/publish/org/${orgId}/dataset/fares/${datasetId}/delete`}
                    >
                      {hasBlockingError ? 'Delete data' : 'Delete data set'}
                    </Link>
                  )}
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

export default function FaresReviewPage({ mapboxToken }: { mapboxToken: string }) {
  return (
    <ProtectedRoute>
      <FaresReviewPageContent mapboxToken={mapboxToken} />
    </ProtectedRoute>
  );
}
