'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useCallback, useEffect } from 'react';
import { ErrorDisplay, LoadingSpinner } from '@/components/shared';
import { useApiResource } from '@/hooks/useApiResource';
import { api } from '@/lib/api-client';
import { publishAppPath } from '@/config/client';
import { formatDateWithOrdinal } from '@/lib/utils/date';

type TimetableUpdateSuccessData = {
  isPtiCompliant: boolean;
  ptiEnforcedDate: string;
};

/** Django `publish.views.timetable.update.RevisionUpdateSuccessView`. */
export function TimetableUpdateSuccessContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const listUrl = publishAppPath(`/publish/org/${orgId}/dataset/timetable`);
  const detailUrl = publishAppPath(`/publish/org/${orgId}/dataset/timetable/${datasetId}`);

  useEffect(() => {
    document.title = 'Data set updated';
  }, []);

  const fetchSuccess = useCallback(
    () => api.get<TimetableUpdateSuccessData>(`/api/publish/timetables/update-success/${orgId}/${datasetId}/`),
    [orgId, datasetId],
  );
  const { data, isLoading, error } = useApiResource(fetchSuccess, 'Failed to load data set');

  if (isLoading) {
    return <LoadingSpinner />;
  }

  if (error || !data) {
    return <ErrorDisplay type="generic" message={error || undefined} />;
  }

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <hr className="govuk-section-break govuk-section-break--m govuk-section-break" />
            <div className="govuk-panel govuk-panel--confirmation">
              <h1 className="govuk-panel__title">Your data set has been successfully updated</h1>
            </div>
            <p className="govuk-body-m">
              {data.isPtiCompliant
                ? 'We have sent you a confirmation email.'
                : `We have sent you a confirmation email. However please note that after ${formatDateWithOrdinal(
                    data.ptiEnforcedDate,
                  )}, BODS won't be accepting any files which are not TransxChange PTI profile v1.1 compliant. Please contact your scheduling supplier to update your data.`}
            </p>
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
            <h2 className="govuk-heading-m">What happens next?</h2>
            <p className="govuk-body-m">
              You can view the data set on your{' '}
              <Link className="govuk-link" href={listUrl}>
                data sets page.
              </Link>{' '}
              or by clicking the button below. The data will now be live for everyone else to see.
            </p>
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break" />
            <Link role="button" className="govuk-button" href={detailUrl}>
              View published data set
            </Link>
            <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
          </div>
          <div className="govuk-!-width-one-third"></div>
        </div>
      </div>
    </div>
  );
}
