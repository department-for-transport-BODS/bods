/**
 * Error Boundary (Django 500 equivalent)
 *
 * Source: transit_odp/templates/500.html (extends error_base.html)
 *
 * Shown when an unhandled error occurs while rendering a page. Django's 500 page
 * has only a heading and a short paragraph - no retry button, homepage button
 * or technical details - so neither does this one.
 */

'use client';

import { useEffect } from 'react';
import Link from 'next/link';
import { wwwPath } from '@/config/client';

const SERVER_ERROR_TITLE = 'Server Error';

interface ErrorProps {
  error: Error & { digest?: string };
  reset?: () => void;
}

export default function Error({ error }: ErrorProps) {
  useEffect(() => {
    console.error('Application error:', error);
  }, [error]);

  // Error boundaries can't export `metadata`; Django's 500.html title_tag is "Server Error".
  useEffect(() => {
    document.title = SERVER_ERROR_TITLE;
  }, []);

  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper app-main-class">
        <div className="govuk-grid-row govuk-!-margin-top-9 govuk-!-margin-bottom-9">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-l">Looks like something went wrong!</h1>

            <p className="govuk-body">
              We track these errors automatically, but if the problem persists feel free to{' '}
              <Link href={wwwPath('/contact')} className="govuk-link">
                contact Bus open data support line
              </Link>
              . In the meantime, try refreshing.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
