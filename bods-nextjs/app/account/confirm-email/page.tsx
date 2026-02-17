/**
 * Email Confirmation Page
 * 
 * Handles email verification links from Django
 */

import { Suspense } from 'react';
import { ConfirmEmailContent } from './ConfirmEmailContent';

export default function ConfirmEmailPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Confirm your email</h1>
            <Suspense fallback={<p className="govuk-body">Loading...</p>}>
              <ConfirmEmailContent />
            </Suspense>
          </div>
        </div>
      </div>
    </div>
  );
}
