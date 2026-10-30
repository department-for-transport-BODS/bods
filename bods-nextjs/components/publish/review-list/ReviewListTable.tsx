'use client';

import Link from 'next/link';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCaretDown, faCaretUp } from '@fortawesome/free-solid-svg-icons';
import { publishAppPath } from '@/config/client';
import { datasetPath } from './reviewListConfig';
import type { ReviewListColumn, ReviewListKind, ReviewListRow } from './types';

const AVL_DATASET_TYPE = 2;

function PieProgress({ id }: { id: number }) {
  return (
    <div className="progress-centre">
      <div id={String(id)} className="pie-progress">
        <svg width="18" height="18">
          <circle r="9" cx="9" cy="9" stroke="none" strokeWidth="0" fill="#7fb19a"></circle>
          <path fill="none" stroke="#006435" strokeWidth="9" strokeLinecap="butt"></path>
        </svg>
        <span className="progress-percent"></span>
        <span className="progress-text">Processing</span>
      </div>
    </div>
  );
}

interface StatusIndicatorProps {
  row: ReviewListRow;
  orgId: string;
  kind: ReviewListKind;
}

/** Port of organisation/snippets/status_indicator.html. */
export function StatusIndicator({ row, orgId, kind }: StatusIndicatorProps) {
  const status = row.status;

  if (status === 'live') {
    const draftStatus = row.draftStatus;
    const isProcessing = draftStatus === 'indexing' || draftStatus === 'pending';
    return (
      <>
        <span className="status-indicator status-indicator--success">Published</span>
        {row.hasDraftRevision && (
          <>
            {' '}
            <a
              className="govuk-link govuk-!-padding-left-1"
              href={publishAppPath(datasetPath(orgId, kind, row.id))}
            >
              View
            </a>
            <div className="govuk-!-padding-top-3">
              {draftStatus === 'success' ? (
                <span className="status-indicator status-indicator--draft">Draft</span>
              ) : isProcessing ? (
                <PieProgress id={row.id} />
              ) : (
                <span className="status-indicator status-indicator--error">Error</span>
              )}
              {!isProcessing && (
                <>
                  {' '}
                  <a
                    className="govuk-link govuk-!-padding-left-1"
                    href={publishAppPath(`${datasetPath(orgId, kind, row.id)}/update/review`)}
                  >
                    View
                  </a>
                </>
              )}
            </div>
          </>
        )}
      </>
    );
  }

  switch (status) {
    case 'indexing':
    case 'pending':
      return <PieProgress id={row.id} />;
    case 'warning':
      return <span className="status-indicator status-indicator--warning">Warning</span>;
    case 'expiring':
      return <span className="status-indicator status-indicator--warning">Soon to expire</span>;
    case 'error':
      return row.datasetType === AVL_DATASET_TYPE ? (
        <span className="status-indicator status-indicator--success">Published</span>
      ) : (
        <span className="status-indicator status-indicator--error">Error</span>
      );
    case 'draft':
    case 'success':
      return <span className="status-indicator status-indicator--draft">Draft</span>;
    case 'expired':
      return <span className="status-indicator status-indicator--inactive">Expired</span>;
    case 'inactive':
      return <span className="status-indicator status-indicator--inactive">Inactive</span>;
    case 'deleted':
      return <span className="status-indicator status-indicator--error">Deleted</span>;
    default:
      return <span>{status}</span>;
  }
}

function withoutTrailingSlash(path: string): string {
  return path.length > 1 ? path.replace(/\/+$/, '') : path;
}

function renderCell(column: ReviewListColumn, row: ReviewListRow, orgId: string, kind: ReviewListKind) {
  switch (column.key) {
    case 'status':
      return <StatusIndicator row={row} orgId={orgId} kind={kind} />;
    case 'name':
      return row.link ? (
        <a className="govuk-link" href={publishAppPath(withoutTrailingSlash(row.link))}>
          {row.name}
        </a>
      ) : (
        row.name
      );
    case 'id':
      return row.id;
    case 'modified':
      return row.modifiedDisplay;
    case 'percent_matching':
      return row.percentMatching ?? '';
    case 'avl_feed_last_checked':
      return row.avlFeedLastCheckedDisplay ?? '';
    case 'short_description':
      return row.shortDescription;
    default:
      return '';
  }
}

function sortHref(searchParams: URLSearchParams, column: ReviewListColumn): string {
  const params = new URLSearchParams(searchParams.toString());
  params.set('sort', column.nextSort ?? column.key);
  params.set('page', '1');
  return `?${params.toString()}`;
}

function ariaSort(direction: ReviewListColumn['direction']) {
  if (direction === 'asc') return 'ascending';
  if (direction === 'desc') return 'descending';
  return 'none';
}

interface ReviewListTableProps {
  kind: ReviewListKind;
  orgId: string;
  columns: ReviewListColumn[];
  rows: ReviewListRow[];
  searchParams: URLSearchParams;
}

/** Port of common/custom_govuk_table.html as rendered by the Django publish list tables. */
export function ReviewListTable({ kind, orgId, columns, rows, searchParams }: ReviewListTableProps) {
  return (
    <div>
      <table className="custom_govuk_table review-list-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            {columns.map((column) => (
              <th
                key={column.key}
                aria-sort={ariaSort(column.direction)}
                role="columnheader"
                scope="col"
                className={[
                  column.direction,
                  'govuk-table__header',
                  column.orderable ? 'orderable' : null,
                ]
                  .filter(Boolean)
                  .join(' ')}
                {...(column.width ? { width: column.width } : {})}
              >
                {column.orderable ? (
                  <Link className="column-header-link" role="button" href={sortHref(searchParams, column)}>
                    {column.label}
                    <span className="hide-using-position">Sort your data by {column.label}</span>
                  </Link>
                ) : (
                  column.label
                )}
                <FontAwesomeIcon icon={faCaretUp} className="order-up" aria-hidden="true" />
                <FontAwesomeIcon icon={faCaretDown} className="order-down" aria-hidden="true" />
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          {rows.map((row, index) => (
            <tr key={row.id} className={`govuk-table__row ${index % 2 === 0 ? 'even' : 'odd'}`}>
              {columns.map((column) => (
                <td key={column.key} className="govuk-table__cell">
                  {renderCell(column, row, orgId, kind)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
