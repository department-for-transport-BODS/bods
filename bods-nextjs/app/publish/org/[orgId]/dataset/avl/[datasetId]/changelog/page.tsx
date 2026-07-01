'use client';

import Link from 'next/link';
import { Fragment, useEffect, useMemo, useState } from 'react';
import { useParams, useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { api } from '@/lib/api-client';
import { formatDateTime } from '@/lib/utils/date';
import { statusIndicatorClass, statusLabel } from '../../_components/avlStatus';

interface ChangelogEntry {
  revisionId: number;
  status: string;
  comment: string;
  updatedAt: string | null;
  errors: string[];
}

interface ChangelogResponse {
  datasetId: number;
  feedName: string;
  count: number;
  page: number;
  pageSize: number;
  totalPages: number;
  hasNext: boolean;
  hasPrevious: boolean;
  results: ChangelogEntry[];
}

function AvlChangelogContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const page = useMemo(() => {
    const pageValue = searchParams.get('page');
    const parsed = pageValue ? parseInt(pageValue, 10) : 1;
    return Number.isNaN(parsed) || parsed < 1 ? 1 : parsed;
  }, [searchParams]);

  const detailUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}`;
  const baseChangelogUrl = `/publish/org/${orgId}/dataset/avl/${datasetId}/changelog`;

  const [state, setState] = useState<{
    isLoading: boolean;
    error: string;
    data: ChangelogResponse | null;
  }>({
    isLoading: true,
    error: '',
    data: null,
  });

  useEffect(() => {
    let isCancelled = false;

    const loadChangelog = async () => {
      setState({ isLoading: true, error: '', data: null });

      try {
        const data = await api.get<ChangelogResponse>(
          `/api/avl/changelog/${orgId}/${datasetId}/?page=${page}`,
        );

        if (!isCancelled) {
          setState({ isLoading: false, error: '', data });
        }
      } catch (err) {
        if (!isCancelled) {
          const message = err instanceof Error ? err.message : 'Unable to load changelog';
          setState({ isLoading: false, error: message, data: null });
        }
      }
    };

    loadChangelog();

    return () => {
      isCancelled = true;
    };
  }, [orgId, datasetId, page]);

  if (state.isLoading) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <p className="govuk-body">Loading changelog...</p>
        </div>
      </div>
    );
  }

  if (state.error || !state.data) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-error-summary" role="alert">
            <h2 className="govuk-error-summary__title">Unable to load changelog</h2>
            <div className="govuk-error-summary__body">
              <p className="govuk-body">{state.error || 'No changelog data found'}</p>
              <Link className="govuk-link" href={detailUrl}>
                Back to feed details
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const data = state.data;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <Link className="govuk-back-link" href={detailUrl}>
          Back
        </Link>

        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <span className="govuk-caption-xl">Changelog</span>
            <h1 className="govuk-heading-xl dont-break-out">{data.feedName || `Feed ${datasetId}`}</h1>
          </div>
        </div>

        <table className="govuk-table custom_govuk_table">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-table__header govuk-!-width-one-third">
                Comment
              </th>
              <th scope="col" className="govuk-table__header">
                Status
              </th>
              <th scope="col" className="govuk-table__header">
                Updated date
              </th>
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {data.results.map((entry) => (
              <Fragment key={entry.revisionId}>
                <tr className="govuk-table__row">
                  <td className="govuk-table__cell">{entry.comment || '-'}</td>
                  <td className="govuk-table__cell">
                    <span className={`status-indicator ${statusIndicatorClass(entry.status)}`}>
                      {statusLabel(entry.status)}
                    </span>
                  </td>
                  <td className="govuk-table__cell">{entry.updatedAt ? formatDateTime(entry.updatedAt) : '-'}</td>
                </tr>
                {entry.status === 'error' && entry.errors.length > 0 && (
                  <tr className="govuk-table__row govuk-table__row--error">
                    <td colSpan={3} className="govuk-table__cell">
                      <ul className="govuk-list govuk-list--error">
                        {entry.errors.map((errorText, index) => (
                          <li key={`${entry.revisionId}-${index}`}>{errorText}</li>
                        ))}
                      </ul>
                    </td>
                  </tr>
                )}
              </Fragment>
            ))}
          </tbody>
        </table>

        {data.totalPages > 1 && (
          <nav className="govuk-pagination" aria-label="Pagination">
            {data.hasPrevious ? (
              <div className="govuk-pagination__prev">
                <Link className="govuk-link govuk-pagination__link" href={`${baseChangelogUrl}?page=${data.page - 1}`} rel="prev">
                  Previous
                </Link>
              </div>
            ) : (
              <div />
            )}

            <p className="govuk-body govuk-!-margin-bottom-0">
              Page {data.page} of {data.totalPages}
            </p>

            {data.hasNext ? (
              <div className="govuk-pagination__next">
                <Link className="govuk-link govuk-pagination__link" href={`${baseChangelogUrl}?page=${data.page + 1}`} rel="next">
                  Next
                </Link>
              </div>
            ) : (
              <div />
            )}
          </nav>
        )}
      </div>
    </div>
  );
}

export default function AvlChangelogPage() {
  return (
    <ProtectedRoute>
      <AvlChangelogContent />
    </ProtectedRoute>
  );
}
