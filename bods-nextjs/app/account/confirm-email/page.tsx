/**
 * Verify Your Email Page
 *
 * Landing page after signup. The verification link in the email points at
 * /account/confirm-email/<key>/, which is handled by the [key] route.
 */

import { VerificationSentContent } from './VerificationSentContent';

export default function VerifyEmailPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Verify your email</h1>
            <VerificationSentContent />
          </div>
        </div>
      </div>
    </div>
  );
}
