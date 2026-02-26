'use client';

/**
 * Global Error Boundary
 *
 *
 * Displays a GDS-styled error page when an unhandled error occurs.
 * Probably can do this better
 */

import { useEffect } from 'react';
import Link from 'next/link';
import { config } from '@/config';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function Error({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  return (
    <div className="govuk-width-container">
      <main className="govuk-main-wrapper" id="main-content" role="main">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">Sorry, there is a problem with the service</h1>

            <p className="govuk-body">Try again later.</p>

            <p className="govuk-body">
              We have not saved your answers. When the service is available, you will have to start again.
            </p>

            <p className="govuk-body">
              If you continue to experience problems, please{' '}
              <Link href="/contact" className="govuk-link">
                contact us
              </Link>
              .
            </p>

            <div className="govuk-button-group">
              <button
                type="button"
                className="govuk-button"
                data-module="govuk-button"
                onClick={() => reset()}
                aria-label="Try again to reload the page"
              >
                Try again
              </button>

              <Link
                href="/"
                className="govuk-button govuk-button--secondary"
                aria-label="Return to the homepage"
              >
                Go to homepage
              </Link>
            </div>

            {config.nodeEnv === 'development' && error.digest && (
              <details className="govuk-details" data-module="govuk-details">
                <summary className="govuk-details__summary">
                  <span className="govuk-details__summary-text">
                    Technical details
                  </span>
                </summary>
                <div className="govuk-details__text">
                  <p className="govuk-body">
                    <strong>Error ID:</strong> {error.digest}
                  </p>
                  <p className="govuk-body">
                    <strong>Message:</strong> {error.message}
                  </p>
                </div>
              </details>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}

