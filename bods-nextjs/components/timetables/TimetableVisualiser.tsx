'use client';

import { useCallback, useMemo, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import type { Timetable } from './line-detail-types';
import { TimetableDateFilter } from './TimetableDateFilter';
import { TimetableJourneyTable, type TooltipControls } from './TimetableJourneyTable';

/**
 * Source: the `is_timetable_visualiser_active` block of
 * transit_odp/publish/templates/publish/revision_review/review_line_metadata.html (publish) and
 * transit_odp/browse/templates/browse/timetables/dataset_detail/review_line_metadata.html (data).
 */
export function TimetableVisualiser({
  timetable,
  feedbackUrl,
  renderEmptyDirections,
}: {
  timetable: Timetable;
  feedbackUrl: string | null;
  renderEmptyDirections: boolean;
}) {
  const searchParams = useSearchParams();
  const [openId, setOpenId] = useState<string | null>(null);
  const close = useCallback(() => setOpenId(null), []);
  const toggle = useCallback((id: string) => setOpenId((current) => (current === id ? null : id)), []);
  const controls: TooltipControls = useMemo(() => ({ openId, toggle, close }), [openId, toggle, close]);

  return (
    <>
      <TimetableDateFilter currDate={timetable.currDate} />
      {!timetable.isTimetableInfoAvailable ? (
        <div className="govuk-inset-text">
          There is no timetable information available to view for this date. Please select another date.
        </div>
      ) : (
        timetable.directions
          .filter((details) => renderEmptyDirections || !details.isEmpty)
          .map((details) => (
            <TimetableJourneyTable
              key={details.direction}
              details={details}
              searchParams={searchParams}
              controls={controls}
              feedbackUrl={feedbackUrl}
            />
          ))
      )}
    </>
  );
}
