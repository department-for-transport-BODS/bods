'use client';

import { useParams } from 'next/navigation';
import { TimetableCancelContent } from './TimetableCreateCancelContent';

export function TimetableUpdateCancelContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const reviewUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}/review`;
  const updateUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}/update`;

  return (
    <TimetableCancelContent
      formUrl={updateUrl}
      confirmUrl={reviewUrl}
      heading="Would you like to cancel updating this data set?"
    />
  );
}