'use client';

/**
 * Data line detail (a published timetable line)
 *
 * Source: transit_odp/browse/templates/browse/timetables/dataset_detail/review_line_metadata.html
 *         transit_odp/browse/templates/browse/base/feedback.html
 * View: transit_odp/browse/views/timetable_views.py - LineMetadataDetailView
 * API: transit_odp/timetables/views/line_detail_api.py - get_browse_timetable_line_detail_api
 */

import { notFound, useParams, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { MapboxRouteMap } from '@/components/data/MapboxRouteMap';
import { ErrorSummary } from '@/components/shared';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { LinePropertyTable } from '@/components/timetables/LinePropertyTable';
import type { DataLineDetail } from '@/components/timetables/line-detail-types';
import { queryWith } from '@/components/timetables/query';
import { TimetableVisualiser } from '@/components/timetables/TimetableVisualiser';
import { dataPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { dataApiPath } from '@/lib/api-paths';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

// Django's truncatechars: keep the result within `length` characters, ending in "…".
function truncateChars(value: string, length: number): string {
  return value.length > length ? `${value.slice(0, length - 1)}…` : value;
}

type Flags = { isTimetableVisualiserActive: boolean; isSpecificFeedback: boolean };

function LineDetail({ isTimetableVisualiserActive, isSpecificFeedback }: Flags) {
  const params = useParams();
  const searchParams = useSearchParams();
  const datasetId = params.id as string;

  const [line, setLine] = useState<DataLineDetail | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  const query = new URLSearchParams(searchParams.toString());
  query.set('includeTimetable', String(isTimetableVisualiserActive));
  const apiPath = dataApiPath(`/api/browser/timetables/${datasetId}/line-detail/?${query.toString()}`);

  useEffect(() => {
    let cancelled = false;
    api
      .get<DataLineDetail>(apiPath)
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

  const feedbackBaseUrl = dataPath(`/timetable/dataset/${datasetId}/feedback/`);
  const isServiceFeedback = searchParams.has('service') && isSpecificFeedback;
  const selfQuery = new URLSearchParams({ line: line.lineName, service: line.serviceCode });

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          'data',
          { label: 'Browse', href: dataPath('/search') },
          { label: 'Timetables Data', href: dataPath('/timetables?status=live') },
          { label: truncateChars(line.datasetName, 19), href: dataPath(`/${datasetId}`) },
          { label: line.lineName, href: dataPath(`/timetable/dataset/${datasetId}/detail?${selfQuery.toString()}`) },
        )}
      />
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl app-!-mb-4 dont-break-out">{line.lineName}</h1>
            <p className="govuk-body app-!-mb-sm-0">Overview of the available bus open data</p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--invisible" />
            <div className="position-relative">
              <MapboxRouteMap
                revisionId={line.revisionId}
                lineName={line.lineName}
                serviceCodes={line.serviceCode}
                containerClassName=""
                ariaLabel={`Interactive map showing the route of ${line.lineName}`}
              />
              <span id="map-updated-timestamp">-</span>
            </div>
            <LinePropertyTable line={line} firstHeaderClassName="govuk-!-width-one-half" />
          </div>
        </div>
        {isTimetableVisualiserActive && line.timetable ? (
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <TimetableVisualiser
                timetable={line.timetable}
                feedbackUrl={isSpecificFeedback ? feedbackBaseUrl : null}
                renderEmptyDirections={false}
              />
            </div>
          </div>
        ) : null}
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h2 className="govuk-heading-m">
              {isServiceFeedback ? 'Noticed issues with this service?' : 'Noticed issues with this data set?'}
            </h2>
            {isServiceFeedback ? (
              <p className="govuk-body">
                You can select a stop code or journey code above to provide feedback about that specific element, or
                you can use this link to provide general feedback about this service.
              </p>
            ) : null}
            <a
              className="govuk-link govuk-!-font-size-19"
              href={isServiceFeedback ? `${feedbackBaseUrl}${queryWith(searchParams, {})}` : feedbackBaseUrl}
            >
              {isServiceFeedback ? 'Provide feedback about this service' : 'Contact data set owner directly'}
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LineDetailPageContent(flags: Flags) {
  return (
    <Suspense fallback={null}>
      <LineDetail {...flags} />
    </Suspense>
  );
}
