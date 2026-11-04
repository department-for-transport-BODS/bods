import Link from 'next/link';
import { publishAppPath } from '@/config/client';
import type { TimetableFeedDetail } from './timetableFeedDetailTypes';

/**
 * Update / deactivate buttons.
 *
 * Source: transit_odp/publish/templates/publish/dataset_detail/success_content.html
 */
export function TimetableFeedDetailActions({ feed }: { feed: TimetableFeedDetail }) {
  const datasetPath = `/org/${feed.orgId}/dataset/timetable/${feed.datasetId}`;
  const canUpdate = feed.datasetStatus !== 'inactive';
  const canDeactivate = feed.datasetStatus !== 'expired' && feed.datasetStatus !== 'inactive';

  return (
    <div className="btn-group-justified">
      {canUpdate ? (
        <Link role="button" className="govuk-button app-!-mr-sm-4" href={publishAppPath(`${datasetPath}/update`)}>
          Update data set
        </Link>
      ) : null}
      {canDeactivate ? (
        <a
          role="button"
          className="govuk-button govuk-button--secondary"
          href={publishAppPath(`${datasetPath}/deactivate`)}
        >
          Deactivate data set
        </a>
      ) : null}
    </div>
  );
}
