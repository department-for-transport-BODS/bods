'use client';

/**
 * Publish-host dataset changelog (timetable and fares)
 *
 * Source: transit_odp/publish/templates/publish/feed_change_log.html (timetable)
 *         transit_odp/fares/templates/fares/feed_change_log.html (fares)
 *         transit_odp/publish/templates/publish/snippets/feed_change_log_table.html
 * Views: transit_odp/publish/views/timetable/changelog.py, transit_odp/fares/views/changelog.py
 * API: get_timetables_changelog_api / get_fares_changelog_api (config/urls/nextjs_api.py)
 *
 * Django renders the same table as the data-host changelog, so the table and the empty
 * breadcrumb/back-link shell are shared with components/data/dataset-subpages.
 */

import { useParams, useSearchParams } from 'next/navigation';
import { Suspense } from 'react';
import { ChangelogTable } from '@/components/data/dataset-subpages/ChangelogPageContent';
import { FeedPageShell } from '@/components/data/dataset-subpages/FeedPageShell';
import type { DatasetChangelog } from '@/components/data/dataset-subpages/types';
import { useSubpageResource } from '@/components/data/dataset-subpages/useSubpageResource';
import { Pagination } from '@/components/shared/Pagination';
import { publishAppPath } from '@/config/client';

export type PublishChangelogKind = 'timetables' | 'fares';

/** Path segment in Django's public URLs: /org/<pk1>/dataset/<segment>/<pk>/ */
const ROUTE_SEGMENT: Record<PublishChangelogKind, string> = {
  timetables: 'timetable',
  fares: 'fares',
};

const LOAD_ERROR = 'Unable to load the changelog. Please refresh and try again.';

function Changelog({ kind }: { kind: PublishChangelogKind }) {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const page = searchParams.get('page');

  const apiPath =
    `/api/publish/${kind}/changelog/${orgId}/${datasetId}/` + (page ? `?page=${encodeURIComponent(page)}` : '');
  const { data, error } = useSubpageResource<DatasetChangelog>(apiPath, LOAD_ERROR);

  const backHref = publishAppPath(`/org/${orgId}/dataset/${ROUTE_SEGMENT[kind]}/${datasetId}/`);

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
        <ChangelogTable data={data} />
        <Pagination currentPage={data.page} totalPages={data.totalPages} variant="table" />
      </div>
    </FeedPageShell>
  );
}

export function PublishChangelogPageContent({ kind }: { kind: PublishChangelogKind }) {
  return (
    <Suspense fallback={null}>
      <Changelog kind={kind} />
    </Suspense>
  );
}
