'use client';

/**
 * Password change success
 *
 * Mirrors Django's account/password_change_done.html.
 */

import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function ChangePasswordDoneContent() {
  const settingsUrl = '/account/settings';

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl govuk-!-margin-bottom-6">Change password</h1>
            <p className="govuk-body-m govuk-!-margin-top-7">Your password has been updated.</p>
            <Link role="button" className="govuk-button" href={settingsUrl}>
              Go back to account settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function ChangePasswordDonePage() {
  return (
    <ProtectedRoute>
      <ChangePasswordDoneContent />
    </ProtectedRoute>
  );
}
