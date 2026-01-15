'use client';

/**
 * Error Display Component
 *
 */

import Link from 'next/link';

type ErrorType = 'network' | 'server' | 'notFound' | 'forbidden' | 'generic';

interface ErrorDisplayProps {
  type?: ErrorType;
  heading?: string;
  message?: string;
  onRetry?: () => void;
  showContactLink?: boolean;
}

const errorDefaults: Record<ErrorType, { heading: string; message: string }> = {
  network: {
    heading: 'Unable to connect',
    message: 'Please check your internet connection and try again.',
  },
  server: {
    heading: 'Something went wrong',
    message: 'We encountered a problem processing your request. Please try again later.',
  },
  notFound: {
    heading: 'Data not found',
    message: 'The information you requested could not be found.',
  },
  forbidden: {
    heading: 'Access denied',
    message: 'You do not have permission to access this resource.',
  },
  generic: {
    heading: 'An error occurred',
    message: 'Something went wrong. Please try again.',
  },
};

export function ErrorDisplay({
  type = 'generic',
  heading,
  message,
  onRetry,
  showContactLink = true,
}: ErrorDisplayProps) {
  const defaults = errorDefaults[type];
  const displayHeading = heading || defaults.heading;
  const displayMessage = message || defaults.message;

  return (
    <div
      className="error-display"
      role="alert"
      aria-live="assertive"
      aria-atomic="true"
    >
      <div className="govuk-error-summary" data-module="govuk-error-summary">
        <div role="alert">
          <h2 className="govuk-error-summary__title">
            {displayHeading}
          </h2>
          <div className="govuk-error-summary__body">
            <p className="govuk-body">{displayMessage}</p>

            <div className="govuk-button-group">
              {onRetry && (
                <button
                  type="button"
                  className="govuk-button"
                  data-module="govuk-button"
                  onClick={onRetry}
                  aria-label="Try loading the data again"
                >
                  Try again
                </button>
              )}

              {showContactLink && (
                <Link
                  href="/contact"
                  className="govuk-link"
                >
                  Contact support
                </Link>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

