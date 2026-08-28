'use client';

/**
 * Account already registered.
 *
 * Mirrors Django's account/account_exists.html (AccountExistsView).
 */

import Link from 'next/link';

export default function AccountExistsPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Account exists</h1>
            <p className="govuk-body-m">
              An account with this email address has already been registered on BODS. Please click
              below to sign in.
            </p>
            <p className="govuk-body-m govuk-!-margin-bottom-6">
              If there are any further issues, please contact the BODS help desk.
            </p>
            <Link href="/account/login" className="govuk-button" data-module="govuk-button">
              Sign in
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
