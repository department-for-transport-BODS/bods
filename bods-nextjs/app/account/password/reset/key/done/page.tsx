'use client';

/**
 * Password reset success.
 *
 * Mirrors Django's account/password_reset_from_key_done.html. The API logs the
 * user in when ACCOUNT_LOGIN_ON_PASSWORD_RESET is true.
 */

import Link from 'next/link';
import { ProtectedRoute } from '@/components/auth/ProtectedRoute';

function PasswordResetKeyDoneContent() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <div className="govuk-panel app-panel--confirmation-nofill">
              <h2 className="govuk-panel__title">Password has been reset</h2>
              <div className="govuk-panel__body">
                Your password has been successfully reset and you have been logged in.
              </div>
            </div>
            <Link href="/account" role="button" draggable="false" className="govuk-button">
              My data account
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function PasswordResetKeyDonePage() {
  return (
    <ProtectedRoute>
      <PasswordResetKeyDoneContent />
    </ProtectedRoute>
  );
}
