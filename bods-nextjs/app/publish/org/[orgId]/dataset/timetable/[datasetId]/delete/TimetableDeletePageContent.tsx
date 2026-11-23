'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { publishAppPath } from '@/config/client';
import { api } from '@/lib/api-client';

interface ReviewStatusResponse {
  name?: string;
  hasLiveRevision?: boolean;
  status?: string;
}

function TimetableDeleteContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const datasetUrl = publishAppPath(`/org/${orgId}/dataset/timetable/${datasetId}`);
  const successUrl = `/publish/org/${orgId}/dataset/timetable/delete-success`;

  const [datasetName, setDatasetName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [hasLiveRevision, setHasLiveRevision] = useState(false);
  const [liveRevisionStatus, setLiveRevisionStatus] = useState('');

  useEffect(() => {
    document.title = 'Delete data set';
  }, []);

  useEffect(() => {
    const statusUrl = `/api/publish/timetables/review-status/${orgId}/${datasetId}/`;
    api
      .get<ReviewStatusResponse>(statusUrl)
      .then(async (data) => {
        setDatasetName(data.name || '');
        const hasLive = Boolean(data.hasLiveRevision);
        setHasLiveRevision(hasLive);
        if (hasLive) {
          // Django's back and cancel targets depend on the live revision's status.
          const live = await api.get<ReviewStatusResponse>(`${statusUrl}?revision=live`);
          setLiveRevisionStatus(live.status || '');
        }
      })
      .catch(() => undefined);
  }, [orgId, datasetId]);

  // Mirrors RevisionDeleteTimetableView.get_cancel_url, which publish/feed_delete.html
  // also uses for the back link: no live revision -> review, live and expired -> dataset
  // detail, any other live status -> update review.
  let cancelUrl = `${datasetUrl}/review`;
  if (hasLiveRevision) {
    cancelUrl = liveRevisionStatus === 'expired' ? datasetUrl : `${datasetUrl}/update/review`;
  }
  // feed_delete.html only switches to the "cancel updating" copy for a non-expired live revision.
  const isCancellingUpdate = hasLiveRevision && liveRevisionStatus !== 'expired';
  const heading = isCancellingUpdate
    ? 'Would you like to cancel updating this data set'
    : 'Would you like to delete this data set?';
  const bodyText = `Please confirm that you would like to ${isCancellingUpdate ? 'cancel updating' : 'delete'} data set "${datasetName}" .`;

  const handleDelete = async () => {
    setIsDeleting(true);
    setErrorMessage('');
    try {
      const data = await api.post<{ redirect?: string }>(
        `/api/publish/timetables/delete/${orgId}/${datasetId}/`,
      );
      const target = data.redirect || successUrl;
      globalThis.location.href = target;
    } catch (error) {
      setErrorMessage(error instanceof Error ? error.message : 'Unable to delete data set. Please try again.');
      setIsDeleting(false);
    }
  };

  return (
    <div className="govuk-width-container">
      <div className="govuk-back-link-wrapper">
        <Link className="govuk-back-link" href={cancelUrl}>Back</Link>
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">{heading}</h1>
            <p className="govuk-body-l">
              {bodyText}
              <br />
              Any changes you have made so far will not be saved.
            </p>
            <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="delete-error-title" />
            <div className="govuk-button-group">
              <button type="button" className="govuk-button" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
              <Link className="govuk-button govuk-button--secondary" href={cancelUrl}>Cancel</Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function TimetableDeletePage() {
  return <ProtectedRoute><TimetableDeleteContent /></ProtectedRoute>;
}
