'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { api } from '@/lib/api-client';

type FaresDetailResponse = {
  datasetId: number;
  status: string;
  name?: string;
  description?: string;
  shortDescription?: string;
  ownerName?: string;
  schemaVersion?: string;
  lastModified?: string;
  lastModifiedUser?: string;
  urlLink?: string;
  downloadUrl?: string;
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

function formatDateTime(value?: string | null): string {
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

  return 'status-indicator--draft';
}

function statusLabel(status?: string) {
  if (!status) {
    return 'Draft';
  }

  if (status === 'live' || status === 'published') {
    return 'Published';
  }

  return status.charAt(0).toUpperCase() + status.slice(1);
}

function FaresDatasetDetailContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const updateDatasetUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/update`;
  const deactivateDatasetUrl = `/publish/org/${orgId}/dataset/fares/${datasetId}/deactivate`;

  const [data, setData] = useState<FaresDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const load = async () => {
      try {
        const payload = await api.get<FaresDetailResponse>(
          `/api/fares/review-status/${orgId}/${datasetId}/?revision=live`,
        );

        if (!isCancelled) {
          setData(payload);
          setError('');
        }
      } catch (err) {
        if (!isCancelled) {
          setError(err instanceof Error ? err.message : 'Unable to load dataset details.');
          setData(null);
        }
      } finally {
        if (!isCancelled) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      isCancelled = true;
    };
  }, [datasetId, orgId]);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Breadcrumbs
          items={[
            { label: 'Bus Open Data Service', href: '/data' },
            { label: 'Publish Bus Open Data', href: '/publish' },
            { label: 'Choose data type', href: `/publish/org/${orgId}/dataset` },
            { label: 'Fares Data Sets', href: `/publish/org/${orgId}/dataset/fares` },
            { label: data?.name || `Dataset ${datasetId}`, current: true, truncateAt: 20 },
          ]}
        />

        {loading ? <p className="govuk-body">Loading dataset details...</p> : null}

        <ErrorSummary errors={error ? [error] : []} summaryId="dataset-detail-error-title" />

        {!loading && !error && data ? (
          <>
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{data.name || `Dataset ${datasetId}`}</h1>
                <p className="govuk-body">Preview your service data status and make changes</p>
              </div>
            </div>

            <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />

            <div className="govuk-grid-row">
              <div className="govuk-grid-column-two-thirds">
                <div className="review-map-placeholder govuk-!-margin-bottom-5" aria-hidden="true">
                  <div className="review-map-placeholder__inner">Map preview</div>
                </div>

                <table className="govuk-table dataset-property-table">
                  <tbody className="govuk-table__body">
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Name</th>
                      <td className="govuk-table__cell dont-break-out">{data.name || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Data set ID</th>
                      <td className="govuk-table__cell dont-break-out">{data.datasetId || datasetId}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Description</th>
                      <td className="govuk-table__cell">{data.description || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Short description</th>
                      <td className="govuk-table__cell">{data.shortDescription || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Status</th>
                      <td className="govuk-table__cell">
                        <span className={`status-indicator ${statusIndicatorClass(data.status)}`}>
                          {statusLabel(data.status)}
                        </span>
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Owner</th>
                      <td className="govuk-table__cell">{data.ownerName || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">NeTEx Version</th>
                      <td className="govuk-table__cell">{data.schemaVersion || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">URL link</th>
                      <td className="govuk-table__cell">
                        {data.urlLink ? (
                          <Link className="govuk-link" href={data.urlLink}>
                            Publisher URL
                          </Link>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Download NeTEx</th>
                      <td className="govuk-table__cell">
                        {data.downloadUrl ? (
                          <Link className="govuk-link" href={data.downloadUrl}>
                            Download .xml
                          </Link>
                        ) : (
                          '-'
                        )}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Last updated</th>
                      <td className="govuk-table__cell">
                        {formatDateTime(data.lastModified)}
                        {data.lastModifiedUser ? ` by ${data.lastModifiedUser}` : ''}
                      </td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Number of fare zones</th>
                      <td className="govuk-table__cell">{data.metadata?.numOfFareZones ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Number of lines</th>
                      <td className="govuk-table__cell">{data.metadata?.numOfLines ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Number of sales offer packages</th>
                      <td className="govuk-table__cell">{data.metadata?.numOfSalesOfferPackages ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Number of fare products</th>
                      <td className="govuk-table__cell">{data.metadata?.numOfFareProducts ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Number of user profiles</th>
                      <td className="govuk-table__cell">{data.metadata?.numOfUserProfiles ?? '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Earliest start date</th>
                      <td className="govuk-table__cell">{formatDateTime(data.metadata?.validFrom) || '-'}</td>
                    </tr>
                    <tr className="govuk-table__row">
                      <th scope="row" className="govuk-table__header">Earliest end date</th>
                      <td className="govuk-table__cell">{formatDateTime(data.metadata?.validTo) || '-'}</td>
                    </tr>
                  </tbody>
                </table>

                <div className="govuk-!-margin-top-9">
                  {data.status === 'inactive' ? null : (
                    <Link
                      className="govuk-button govuk-!-margin-right-3"
                      href={updateDatasetUrl}
                    >
                      Update data set
                    </Link>
                  )}
                  {data.status === 'expired' || data.status === 'inactive' ? null : (
                    <Link
                      className="govuk-button govuk-button--secondary"
                      href={deactivateDatasetUrl}
                    >
                      Deactivate data set
                    </Link>
                  )}
                </div>
              </div>

              <div className="govuk-grid-column-one-third govuk-!-padding-top-5">
                <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
                <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                  <li>
                    <Link className="govuk-link" href="/publish/guide-me">
                      View our guidelines here
                    </Link>
                  </li>
                  <li>
                    <Link className="govuk-link" href="/publish/account">
                      Contact support desk
                    </Link>
                  </li>
                </ul>
              </div>
            </div>
          </>
        ) : null}
      </div>
    </div>
  );
}

export default function FaresDatasetDetailPage() {
  return (
    <ProtectedRoute>
      <FaresDatasetDetailContent />
    </ProtectedRoute>
  );
}
