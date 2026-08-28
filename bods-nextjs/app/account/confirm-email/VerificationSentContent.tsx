/**
 * Verification Sent Content Component
 *
 * Shown after signup, mirroring Django's EmailVerificationSentView. The address
 * is stashed by the signup page rather than the server session.
 */

'use client';

import { useSyncExternalStore } from 'react';
import { HOSTS } from '@/config/client';
import { useBodsArea } from '@/lib/bods-host-context';
import {
  readVerificationEmail,
  subscribeToVerificationEmail,
  verificationEmailServerSnapshot,
} from '@/lib/auth/verification-email';

export function VerificationSentContent() {
  const area = useBodsArea();
  const email = useSyncExternalStore(
    subscribeToVerificationEmail,
    readVerificationEmail,
    verificationEmailServerSnapshot
  );

  return (
    <>
      <p className="govuk-body-m">
        We have sent an email to {email ? `${email} ` : 'your email address '}
        to verify your address. Please click the link in the email to continue.
      </p>
      <p className="govuk-body-m govuk-!-margin-bottom-6">
        If you cannot find the email then look in your spam or junk email folder.
      </p>
      <a href={HOSTS[area]} className="govuk-button" data-module="govuk-button">
        Home
      </a>
    </>
  );
}
