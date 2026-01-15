/**
 * 404 Not Found Page
 *
 *
 * Displays a GDS-styled 404 page when a user navigates to a non-existent page.
 */

import Link from 'next/link';

export default function NotFound() {
  return (
    <div className="govuk-width-container">
      <main className="govuk-main-wrapper" id="main-content" role="main">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Page not found</h1>

            <p className="govuk-body">
              If you typed the web address, check it is correct.
            </p>

            <p className="govuk-body">
              If you pasted the web address, check you copied the entire address.
            </p>

            <p className="govuk-body">
              If the web address is correct or you selected a link or button,{' '}
              <Link href="/contact" className="govuk-link">
                contact us
              </Link>{' '}
              if you need to speak to someone about the service.
            </p>

            <div className="govuk-button-group">
              <Link
                href="/"
                className="govuk-button"
                data-module="govuk-button"
                aria-label="Return to the homepage"
              >
                Go to homepage
              </Link>
            </div>

            <h2 className="govuk-heading-m">Looking for something specific?</h2>

            <ul className="govuk-list">
              <li>
                <Link href="/data" className="govuk-link">
                  Browse bus data
                </Link>
              </li>
              <li>
                <Link href="/publish" className="govuk-link">
                  Publish bus data
                </Link>
              </li>
              <li>
                <Link href="/guidance/support/bus-operators" className="govuk-link">
                  Guidance for bus operators
                </Link>
              </li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  );
}

