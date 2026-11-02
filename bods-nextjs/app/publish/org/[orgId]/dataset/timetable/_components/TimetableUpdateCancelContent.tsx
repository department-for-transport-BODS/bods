'use client';

import { useParams } from 'next/navigation';
import { TimetableCancelContent } from './TimetableCreateCancelContent';

type TimetableUpdateCancelContentProps = {
  /** Cancelling from `update/review/update` returns to `update/review`. */
  isUpdateReview?: boolean;
};

export function TimetableUpdateCancelContent({ isUpdateReview = false }: Readonly<TimetableUpdateCancelContentProps>) {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const datasetUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}`;
  const reviewUrl = isUpdateReview ? `${datasetUrl}/update/review` : `${datasetUrl}/review`;
  const updateUrl = isUpdateReview ? `${datasetUrl}/update/review/update` : `${datasetUrl}/update`;

  return (
    <TimetableCancelContent
      formUrl={updateUrl}
      confirmUrl={reviewUrl}
      heading="Would you like to cancel updating this data set?"
    />
  );
}
