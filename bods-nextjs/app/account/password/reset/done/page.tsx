'use client';

/**
 * Password reset email sent.
 *
 * Mirrors Django's account/password_reset_done.html.
 */

import { useSyncExternalStore } from 'react';
import { HOSTS } from '@/config/client';
import { useBodsArea } from '@/lib/bods-host-context';
import {
  passwordResetEmailServerSnapshot,
  readPasswordResetEmail,
  subscribeToPasswordResetEmail,
} from '@/lib/auth/password-reset';

export default function PasswordResetDonePage() {
  const area = useBodsArea();
  const email = useSyncExternalStore(
    subscribeToPasswordResetEmail,
    readPasswordResetEmail,
    passwordResetEmailServerSnapshot,
  );

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Reset password link has been sent</h1>
            <p className="govuk-body-m">
              If this email address exists in our system we will have sent a password reset email to{' '}
              {email || 'you'}. Check your email and follow the link within 24 hours to reset your
              password.
            </p>
            <p className="govuk-body-m govuk-!-margin-bottom-6">
              If you cannot find the email then look in your spam or junk email folder.
            </p>
            <a href={HOSTS[area]} role="button" draggable="false" className="govuk-button">
              Home
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
