'use client';

/**
 * Dataset changelog (data host)
 *
 * Source: transit_odp/browse/templates/browse/{timetables,avl,fares}/feed_change_log.html
 *         transit_odp/publish/templates/publish/snippets/feed_change_log_table.html
 * View: transit_odp/browse/views/{timetable,avl,fares}_views.py - ChangeLogView
 * API: transit_odp/browse/views/dataset_subpages_api.py - get_dataset_changelog_api
 */

import { useParams, useSearchParams } from 'next/navigation';
import { Fragment, Suspense, useEffect } from 'react';
import { Pagination } from '@/components/shared/Pagination';
import { FeedPageShell } from './FeedPageShell';
import { datasetDetailHref, datasetSubpageApiPath, datasetSubpageHref, type DatasetSubpageKind } from './kinds';
import type { ChangelogDataQuality, ChangelogRow, DatasetChangelog } from './types';
import { useSubpageResource } from './useSubpageResource';

const LOAD_ERROR = 'Unable to load the changelog. Please refresh and try again.';

function DataQualityCell({ dataQuality }: { dataQuality?: ChangelogDataQuality }) {
  if (!dataQuality || dataQuality.text !== undefined) return <>{dataQuality?.text}</>;

  return (
    <>
      {dataQuality.score}{' '}
      <span className={`status-indicator status-indicator--${dataQuality.indicator} govuk-!-font-weight-bold`}>
        {dataQuality.ragLevel}
      </span>
    </>
  );
}

function ChangelogTableRow({ row, showDataQuality }: { row: ChangelogRow; showDataQuality: boolean }) {
  return (
    <>
      <tr className="govuk-table__row">
        <td className="govuk-table__cell">{row.comment}</td>
        <td className="govuk-table__cell">
          <span className={`status-indicator ${row.statusClass}`}>{row.statusLabel}</span>
        </td>
        <td className="govuk-table__cell">
          <div>{row.updatedAt}</div>
        </td>
        {showDataQuality ? (
          <td className="govuk-table__cell">
            <DataQualityCell dataQuality={row.dataQuality} />
          </td>
        ) : null}
      </tr>
      {row.showErrors ? (
        // Django hard-codes colspan="4" for every dataset type.
        <tr className="govuk-table__row govuk-table__row--error">
          <td colSpan={4} className="govuk-table__cell">
            <ul className="govuk-list govuk-list--error">
              {row.errors.map((description, index) => (
                <li key={`${row.revisionId}-${index}`}>{description}</li>
              ))}
            </ul>
          </td>
        </tr>
      ) : null}
    </>
  );
}

function Changelog({ kind }: { kind: DatasetSubpageKind }) {
  const params = useParams();
  const searchParams = useSearchParams();
  const datasetId = params.id as string;
  const page = searchParams.get('page');

  const apiPath = datasetSubpageApiPath(kind, datasetId, 'changelog') + (page ? `?page=${encodeURIComponent(page)}` : '');
  const { data, error } = useSubpageResource<DatasetChangelog>(apiPath, LOAD_ERROR);

  const backHref = datasetDetailHref(kind, datasetId);

  if (!data) {
    return <FeedPageShell backHref={backHref} error={error} />;
  }

  return (
    <FeedPageShell backHref={backHref}>
      <div className="govuk-grid-row">
        <div className="govuk-grid-column-full">
          <span className="govuk-caption-xl">Changelog</span>
          <h1 className="govuk-heading-xl dont-break-out">{data.name}</h1>
        </div>
      </div>
      <div>
        {/* Django's SCSS makes custom_govuk_table @extend .govuk-table; plain CSS needs both classes. */}
        <table className="govuk-table custom_govuk_table">
          <thead className="govuk-table__head">
            <tr className="govuk-table__row">
              <th scope="col" className="govuk-!-width-one-third govuk-table__header">
                Comment
              </th>
              <th scope="col" className="govuk-table__header">
                Status
              </th>
              <th scope="col" className="govuk-table__header">
                Updated date
              </th>
              {data.showDataQuality ? (
                <th scope="col" className="govuk-table__header">
                  Data quality
                </th>
              ) : null}
            </tr>
          </thead>
          <tbody className="govuk-table__body">
            {data.results.map((row) => (
              <Fragment key={row.revisionId}>
                <ChangelogTableRow row={row} showDataQuality={data.showDataQuality} />
              </Fragment>
            ))}
          </tbody>
        </table>
        <Pagination
          currentPage={data.page}
          totalPages={data.totalPages}
          showSinglePage
          baseUrl={datasetSubpageHref(kind, datasetId, 'changelog')}
        />
      </div>
    </FeedPageShell>
  );
}

export function ChangelogPageContent({ kind }: { kind: DatasetSubpageKind }) {
  useEffect(() => {
    document.title = 'Changelog';
  }, []);

  return (
    <Suspense fallback={null}>
      <Changelog kind={kind} />
    </Suspense>
  );
}
