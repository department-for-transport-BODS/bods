'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';
import { ErrorSummary } from '@/components/shared';
import { api } from '@/lib/api-client';

function TimetableDeleteContent() {
  const params = useParams();
  const orgId = params.orgId as string;
  const datasetId = params.datasetId as string;
  const reviewUrl = `/publish/org/${orgId}/dataset/timetable/${datasetId}/review`;
  const successUrl = `/publish/org/${orgId}/dataset/timetable/delete-success`;

  const [datasetName, setDatasetName] = useState('');
  const [isDeleting, setIsDeleting] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    api.get<{ name?: string }>(`/api/publish/timetables/review-status/${orgId}/${datasetId}/`)
      .then((data) => setDatasetName(data.name || ''))
      .catch(() => undefined);
  }, [orgId, datasetId]);

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
        <Link className="govuk-back-link" href={reviewUrl}>Back</Link>
      </div>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-full">
            <h1 className="govuk-heading-xl">Would you like to delete this data set?</h1>
            <p className="govuk-body-l">Please confirm that you would like to delete data set &quot;{datasetName}&quot;. Any changes you have made so far will not be saved.</p>
            <ErrorSummary errors={errorMessage ? [errorMessage] : []} summaryId="delete-error-title" />
            <div className="govuk-button-group">
              <button type="button" className="govuk-button" onClick={handleDelete} disabled={isDeleting}>
                {isDeleting ? 'Deleting...' : 'Delete'}
              </button>
              <Link role="button" className="govuk-button govuk-button--secondary" href={reviewUrl}>Cancel</Link>
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
