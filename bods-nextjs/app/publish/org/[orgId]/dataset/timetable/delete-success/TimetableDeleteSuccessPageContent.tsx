'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect } from 'react';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

export default function TimetableDeleteSuccessPage() {
  const params = useParams();
  const orgId = params.orgId as string;

  useEffect(() => {
    document.title = 'Data set deleted';
  }, []);

  return (
    <ProtectedRoute>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper">
          <div className="govuk-grid-row">
            <div className="govuk-grid-column-full">
              <h1 className="govuk-heading-xl">Data set has been deleted</h1>
              <p className="govuk-body-l">Data set has been deleted.</p>
              <Link role="button" className="govuk-button govuk-!-margin-top-5" href={`/publish/org/${orgId}/dataset/timetable`}>
                Go back to your data sets
              </Link>
            </div>
          </div>
        </div>
      </div>
    </ProtectedRoute>
  );
}
