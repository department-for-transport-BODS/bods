// This file implements the "Review and publish" page for a fares dataset in the BODS Next.js frontend
// It fetches the processing status of the uploaded dataset from a custom API route, 
// displays relevant information and metadata about the dataset, 
// and allows the user to publish it once they have reviewed the details. The page also includes error handling and links to support resources.
'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useMemo, useRef, useState } from 'react';
import type { StopPoint } from '@/components/data/StopMap';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { config } from '@/config';

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
};

const PUBLISHED_STATUSES = new Set(['live', 'expiring', 'warning']);

const POLL_INTERVAL_MS = 1000;

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
  token: string | null;
  mapboxToken: string;
};

function FaresStopMapPreview({ revisionId, token, mapboxToken }: Readonly<FaresStopMapPreviewProps>) {
  const [fareStops, setFareStops] = useState<StopPoint[]>([]);
  const [isMapLoading, setIsMapLoading] = useState(false);
  const [hasLoadedStops, setHasLoadedStops] = useState(false);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);
  const mapRef = useRef<InstanceType<(typeof import('mapbox-gl'))['default']['Map']> | null>(null);

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
    if (!revisionId || !token) {
      return;
    }

    let isCancelled = false;

    const loadFareStops = async () => {
      setIsMapLoading(true);
      setHasLoadedStops(false);
      try {
        const response = await fetch(`/api/fares/stop-points?revisionId=${revisionId}`, {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        });

        const payload = (await response.json().catch(() => ({}))) as FareStopsApiResponse;
        if (!isCancelled) {
          setFareStops(response.ok ? parseFareStops(payload) : []);
          setHasLoadedStops(response.ok);
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
  }, [revisionId, token]);

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

function formatDateTime(value?: string | null) {
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
}

function statusIndicatorClass(status?: string) {
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
}

function statusLabel(status?: string) {
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
}

type CancelToken = { value: boolean };
type PollingHandle = { interval: ReturnType<typeof setInterval> | undefined };

type FetchStatusCallbacks = Readonly<{
  setStatusData: (data: ReviewStatusResponse) => void;
  setErrorMessage: (msg: string) => void;
  setIsInitialLoading: (v: boolean) => void;
}>;

async function fetchFaresStatus(
  token: string | null,
  orgId: string,
  datasetId: string,
  cancel: CancelToken,
  polling: PollingHandle,
  cb: FetchStatusCallbacks,
) {
  if (!token) {
    if (!cancel.value) {
      cb.setErrorMessage('Not authenticated. Please sign in and retry.');
      cb.setIsInitialLoading(false);
    }
    return;
  }
  try {
    const resp = await fetch(`/api/fares/review-status?orgId=${orgId}&datasetId=${datasetId}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await resp.json().catch(() => ({}))) as ReviewStatusResponse & { error?: string };
    if (!resp.ok) {
      if (!cancel.value) {
        cb.setErrorMessage(data.error || `Status check failed (${resp.status}).`);
        cb.setIsInitialLoading(false);
      }
      return;
    }
    if (!cancel.value) {
      cb.setStatusData(data);
      cb.setErrorMessage('');
      cb.setIsInitialLoading(false);
    }
    if (!data.loading && polling.interval) {
      clearInterval(polling.interval);
    }
  } catch {
    if (!cancel.value) {
      cb.setErrorMessage('Unable to check processing status. Please refresh and try again.');
      cb.setIsInitialLoading(false);
    }
  }
}

async function publishFaresDataset(
  token: string,
  orgId: string,
  datasetId: string,
  faresListUrl: string,
  setIsPublishing: (v: boolean) => void,
  setErrorMessage: (v: string) => void,
) {
  try {
    const resp = await fetch(`/api/fares/publish?orgId=${orgId}&datasetId=${datasetId}`, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
    });
    const data = (await resp.json().catch(() => ({}))) as { error?: string; redirect?: string };
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
}

type ReviewAreaStatus = Readonly<{ isInitialLoading: boolean; loading: boolean; progress: number }>;
type ReviewAreaPublish = Readonly<{
  hasReviewed: boolean;
  isPublishing: boolean;
  isPublishDisabled: boolean;
  onReviewChange: (checked: boolean) => void;
  onPublish: () => void;
}>;

function ReviewDataArea({
  areaStatus,
  statusData,
  validationErrorMessage,
  publish,
  token,
  orgId,
  datasetId,
}: Readonly<{
  areaStatus: ReviewAreaStatus;
  statusData: ReviewStatusResponse | null;
  validationErrorMessage: string | null;
  publish: ReviewAreaPublish;
  token: string | null;
  orgId: string;
  datasetId: string;
}>) {
  if (areaStatus.isInitialLoading) {
    return <p className="govuk-body">Loading...</p>;
  }

  if (areaStatus.loading) {
    return (
      <div className="govuk-panel govuk-panel--confirmation">
        <h2 className="govuk-panel__title govuk-!-font-size-36">Your data is being processed</h2>
        <div className="govuk-panel__body govuk-!-font-size-19">
          <div className="pb3-l">
            The data format is being checked to confirm it is NeTEx.
            <br />
            Once successfully validated the data set details will
            <br />
            be shown here.
          </div>
          <div
            id="progressOuterDiv"
            style={{
              width: '100%',
              height: '20px',
              backgroundColor: '#1d70b8',
              borderRadius: '2px',
              margin: '12px 0 8px',
            }}
          >
            <div
              id="progressInnerDiv"
              style={{
                width: `${areaStatus.progress}%`,
                height: '100%',
                backgroundColor: '#ffffff',
                borderRadius: '2px 0 0 2px',
                transition: 'width 0.3s ease',
              }}
            />
          </div>
          <span id="progressSpan" style={{ color: '#ffffff', fontWeight: 'bold' }}>
            {areaStatus.progress}%
          </span>
        </div>
      </div>
    );
  }

  return (
    <>
      {statusData?.error && validationErrorMessage ? (
        <div className="app-dqs-panel govuk-!-margin-bottom-7">
          <div className="app-dqs-panel__body">
            <p className="govuk-body govuk-!-margin-bottom-0">{validationErrorMessage}</p>
          </div>
        </div>
      ) : null}

      <div className="govuk-!-margin-bottom-6">
        <div className="govuk-checkboxes" data-module="govuk-checkboxes">
          <div className="govuk-checkboxes__item">
            <input
              className="govuk-checkboxes__input"
              id="publish-review-confirmation"
              name="publish-review-confirmation"
              type="checkbox"
              checked={publish.hasReviewed}
              onChange={(event) => publish.onReviewChange(event.target.checked)}
            />
            <label className="govuk-label govuk-checkboxes__label" htmlFor="publish-review-confirmation">
              I have reviewed the submission and wish to publish my data
            </label>
          </div>
        </div>

        <button
          type="button"
          className="govuk-button"
          onClick={publish.onPublish}
          disabled={publish.isPublishDisabled}
        >
          {publish.isPublishing ? 'Publishing...' : 'Publish data'}
        </button>
      </div>

      <h2 className="govuk-heading-l dont-break-out">{statusData?.name || 'Unnamed fares dataset'}</h2>

      <FaresStopMapPreview
        revisionId={statusData?.revisionId}
        token={token}
        mapboxToken={config.mapboxToken}
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

      <div className="govuk-button-group">
        {PUBLISHED_STATUSES.has(statusData?.status ?? '') ? null : (
          <Link className="govuk-button govuk-button--secondary" href={`/publish/org/${orgId}/dataset/fares/${datasetId}/delete`}>
            Delete data set
          </Link>
        )}
      </div>
    </>
  );
}

function FaresReviewPageContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const faresListUrl = `/publish/org/${orgId}/dataset/fares`;
  const supportBusOperatorsUrl = '/publish/guide-me';
  const contactSupportUrl = '/publish/account';

  const [statusData, setStatusData] = useState<ReviewStatusResponse | null>(null);
  const [isInitialLoading, setIsInitialLoading] = useState(true);
  const [isPublishing, setIsPublishing] = useState(false);
  const [hasReviewed, setHasReviewed] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const loading = statusData?.loading ?? true;
  const progress = Math.max(0, Math.min(100, statusData?.progress ?? 0));
  const validationErrorMessage = statusData?.errorDescription || null;

  const token = useMemo(() => {
    if (!globalThis.window) {
      return null;
    }

    return globalThis.window.localStorage.getItem('bods.auth.access');
  }, []);

  useEffect(() => {
    const cancel: CancelToken = { value: false };
    const polling: PollingHandle = { interval: undefined };
    const cb: FetchStatusCallbacks = { setStatusData, setErrorMessage, setIsInitialLoading };
    const runFetch = () => fetchFaresStatus(token, orgId, datasetId, cancel, polling, cb);
    runFetch();
    polling.interval = setInterval(runFetch, POLL_INTERVAL_MS);
    return () => {
      cancel.value = true;
      clearInterval(polling.interval);
    };
  }, [datasetId, orgId, token]);

  const isPublishDisabled = isPublishing || !hasReviewed;

  const handlePublish = () => {
    if (!token || isPublishing) return;
    setIsPublishing(true);
    setErrorMessage('');
    publishFaresDataset(token, orgId, datasetId, faresListUrl, setIsPublishing, setErrorMessage);
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
            <ReviewDataArea
              areaStatus={{ isInitialLoading, loading, progress }}
              statusData={statusData}
              validationErrorMessage={validationErrorMessage}
              publish={{ hasReviewed, isPublishing, isPublishDisabled, onReviewChange: setHasReviewed, onPublish: handlePublish }}
              token={token}
              orgId={orgId}
              datasetId={datasetId}
            />
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
