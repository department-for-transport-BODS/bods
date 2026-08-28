/**
 * Email Confirmation Page
 *
 * Target of the verification link in the signup email.
 * Django: `/account/confirm-email/<key>/`
 */

'use client';

import { useParams } from 'next/navigation';
import { ConfirmEmailContent } from '../ConfirmEmailContent';

export default function ConfirmEmailPage() {
  const params = useParams();
  const confirmationKey = params.key as string;

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Confirm email address</h1>
            <ConfirmEmailContent confirmationKey={confirmationKey} />
          </div>
        </div>
      </div>
    </div>
  );
}
