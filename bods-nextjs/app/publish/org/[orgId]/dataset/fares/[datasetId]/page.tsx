'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

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

  const [data, setData] = useState<FaresDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    let isCancelled = false;

    const load = async () => {
      try {
        const token = globalThis.window.localStorage.getItem('bods.auth.access');
        const response = await fetch(`/api/fares/review-status?orgId=${orgId}&datasetId=${datasetId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });

        const payload = (await response.json().catch(() => ({}))) as FaresDetailResponse & { error?: string };

        if (!response.ok) {
          throw new Error(payload.error || `Unable to load dataset (${response.status})`);
        }

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
        <div className="govuk-breadcrumbs">
          <ol className="govuk-breadcrumbs__list">
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/data">
                Bus Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href="/publish">
                Publish Open Data Service
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset`}>
                Choose data type
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item">
              <Link className="govuk-breadcrumbs__link" href={`/publish/org/${orgId}/dataset/fares`}>
                Fares Data Sets
              </Link>
            </li>
            <li className="govuk-breadcrumbs__list-item" aria-current="page">
              {(data?.name || `Dataset ${datasetId}`).slice(0, 20)}
            </li>
          </ol>
        </div>

        {loading ? <p className="govuk-body">Loading dataset details...</p> : null}

        {error ? (
          <div className="govuk-error-summary" role="alert" aria-labelledby="dataset-detail-error-title">
            <h2 className="govuk-error-summary__title" id="dataset-detail-error-title">
              There is a problem
            </h2>
            <div className="govuk-error-summary__body">
              <ul className="govuk-list govuk-error-summary__list">
                <li>{error}</li>
              </ul>
            </div>
          </div>
        ) : null}

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
                      <th scope="row" className="govuk-table__header">Last updated</th>
                      <td className="govuk-table__cell">
                        {formatDateTime(data.lastModified)}
                        {data.lastModifiedUser ? ` by ${data.lastModifiedUser}` : ''}
                      </td>
                    </tr>
                  </tbody>
                </table>
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
