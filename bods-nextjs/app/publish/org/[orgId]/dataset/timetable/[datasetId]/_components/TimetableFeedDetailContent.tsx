'use client';

import { notFound, useParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { OperatorRequirementsHelp } from '@/components/publish/OperatorRequirementsHelp';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { publishAppPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { TimetableFeedDetailActions } from './TimetableFeedDetailActions';
import { TimetableFeedDetailErrorPanel } from './TimetableFeedDetailErrorPanel';
import { TimetableFeedDetailTable } from './TimetableFeedDetailTable';
import { TimetableServiceNumbers } from './TimetableServiceNumbers';
import type { TimetableFeedDetail } from './timetableFeedDetailTypes';

export type { TimetableFeedDetail } from './timetableFeedDetailTypes';

/**
 * Publish timetable data set detail page.
 *
 * Source: transit_odp/publish/templates/publish/dataset_detail/index.html
 * View: transit_odp/publish/views/timetable/detail.py - FeedDetailView
 * API: transit_odp/publish/views/timetable_feed_detail_api.py
 */
export function TimetableFeedDetailContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [feed, setFeed] = useState<TimetableFeedDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    let cancelled = false;
    api
      .get<TimetableFeedDetail>(`/api/publish/timetables/feed-detail/${orgId}/${datasetId}/`)
      .then((data) => {
        if (cancelled) return;
        setFeed(data);
        setErrorMessage(null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 404) {
          setMissing(true);
          return;
        }
        setErrorMessage('Unable to load the data set details. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, [orgId, datasetId]);

  useEffect(() => {
    document.title = 'Data set details';
  }, []);

  if (missing) notFound();

  if (!feed) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="feed-detail-error-title" />
        </div>
      </div>
    );
  }

  const datasetPath = `/org/${orgId}/dataset/timetable/${datasetId}`;

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          'publish',
          { label: 'Choose data type', href: publishAppPath(`/org/${orgId}/dataset`) },
          { label: 'Timetables Data Sets', href: publishAppPath(`/org/${orgId}/dataset/timetable`) },
          { label: feed.name, href: publishAppPath(datasetPath), truncateAt: 20 },
        )}
      />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{feed.name}</h1>
            <p className="govuk-body app-!-mb-sm-0">Preview your service data status and make changes</p>
          </div>
        </div>
        <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            {feed.status === 'error' ? (
              <TimetableFeedDetailErrorPanel feed={feed} />
            ) : (
              <>
                <MapboxRouteMap
                  revisionId={feed.liveRevisionId}
                  containerClassName=""
                  ariaLabel={`Interactive map showing the routes of ${feed.name}`}
                />
                <TimetableFeedDetailTable feed={feed} />
                <TimetableServiceNumbers
                  orgId={feed.orgId}
                  datasetId={feed.datasetId}
                  distinctAttributes={feed.distinctAttributes}
                />
                <TimetableFeedDetailActions feed={feed} />
              </>
            )}
          </div>
          <div className="govuk-grid-column-one-third">
            <OperatorRequirementsHelp />
          </div>
        </div>
      </div>
    </div>
  );
}
