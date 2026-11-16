'use client';

/**
 * Organisation profile updated.
 *
 * Mirrors Django's organisation/organisation_form_success.html
 * (OrgProfileEditSuccessView). `pk` is the organisation id.
 */

import { useParams } from 'next/navigation';
import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function OrganisationProfileEditSuccessContent() {
  const params = useParams();
  const orgId = params.pk as string;
  const profileUrl = `/account/manage/org-profile/${orgId}`;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">
              Organisation details have been updated
            </h1>
            <Link role="button" className="govuk-button" href={profileUrl}>
              Go back to organisation profile
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function OrganisationProfileEditSuccessPage() {
  return (
    <ProtectedRoute>
      <OrganisationProfileEditSuccessContent />
    </ProtectedRoute>
  );
}
