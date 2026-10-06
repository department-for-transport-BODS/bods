'use client';

/**
 * Publish line detail (preview of a line in a timetable revision under review)
 *
 * Source: transit_odp/publish/templates/publish/revision_review/review_line_metadata.html
 * View: transit_odp/timetables/views/review.py - LineMetadataRevisionView
 * API: transit_odp/timetables/views/line_detail_api.py - get_timetables_line_detail_api
 */

import { notFound, useParams, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { LinePropertyTable } from '@/components/timetables/LinePropertyTable';
import type { PublishLineDetail } from '@/components/timetables/line-detail-types';
import { TimetableVisualiser } from '@/components/timetables/TimetableVisualiser';
import { publishAppPath, wwwPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

function LineDetail({ isTimetableVisualiserActive }: { isTimetableVisualiserActive: boolean }) {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;

  const [line, setLine] = useState<PublishLineDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  const query = new URLSearchParams(searchParams.toString());
  query.set('includeTimetable', String(isTimetableVisualiserActive));
  const apiPath = `/api/publish/timetables/line-detail/${orgId}/${datasetId}/?${query.toString()}`;

  useEffect(() => {
    let cancelled = false;
    api
      .get<PublishLineDetail>(apiPath)
      .then((data) => {
        if (cancelled) return;
        setLine(data);
        setErrorMessage(null);
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 404) {
          setMissing(true);
          return;
        }
        setErrorMessage('Unable to load the service details. Please refresh and try again.');
      });
    return () => {
      cancelled = true;
    };
  }, [apiPath]);

  useEffect(() => {
    if (line) document.title = line.lineName;
  }, [line]);

  if (missing) notFound();

  if (!line) {
    return (
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="line-detail-error-title" />
        </div>
      </div>
    );
  }

  const datasetPath = `/org/${orgId}/dataset/timetable/${datasetId}`;
  const selfQuery = new URLSearchParams({
    line: line.lineName,
    revision_id: String(line.revisionId),
    service: line.serviceCode,
  });

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          'publish',
          { label: 'Choose data type', href: publishAppPath(`/org/${orgId}/dataset`) },
          { label: 'Timetables Data Sets', href: publishAppPath(`/org/${orgId}/dataset/timetable`) },
          { label: line.feedName, href: publishAppPath(`${datasetPath}/review`), truncateAt: 20 },
          { label: line.lineName, href: publishAppPath(`${datasetPath}/review/detail?${selfQuery.toString()}`) },
        )}
      />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{line.lineName}</h1>
            <p className="govuk-body app-!-mb-sm-0">Preview your service data status and make changes</p>
          </div>
        </div>
        <hr className="govuk-section-break govuk-section-break--l govuk-section-break--invisible" />
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <MapboxRouteMap
              revisionId={line.revisionId}
              lineName={line.lineName}
              serviceCodes={line.serviceCode}
              containerClassName=""
              ariaLabel={`Interactive map showing the route of ${line.lineName}`}
            />
            <LinePropertyTable line={line} />
          </div>
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need help with operator data requirements?</h2>
            <ul className="govuk-list app-list--nav govuk-!-font-size-19">
              <li>
                <a className="govuk-link" href={publishAppPath('/guidance/operator-requirements')}>
                  View our guidelines here
                </a>
              </li>
              <li>
                <a className="govuk-link" href={wwwPath('/contact')}>
                  Contact support desk
                </a>
              </li>
            </ul>
          </div>
          {isTimetableVisualiserActive && line.timetable ? (
            <div className="govuk-grid-row">
              <div className="govuk-grid-column-full">
                <TimetableVisualiser timetable={line.timetable} feedbackUrl={null} renderEmptyDirections />
              </div>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}

export default function LineDetailPageContent({ isTimetableVisualiserActive }: { isTimetableVisualiserActive: boolean }) {
  return (
    <ProtectedRoute>
      <Suspense fallback={null}>
        <LineDetail isTimetableVisualiserActive={isTimetableVisualiserActive} />
      </Suspense>
    </ProtectedRoute>
  );
}
