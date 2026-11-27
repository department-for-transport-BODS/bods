import Link from 'next/link';
import type { ReactNode } from 'react';
import { ErrorSummary } from '@/components/shared';

interface FeedPageShellProps {
  /** Target of the "Back" link; omit for pages without one. */
  backHref?: string;
  /** Message shown instead of the page when it could not be loaded. */
  error?: string | null;
  children?: ReactNode;
}

/**
 * Layout shared by the dataset sub-pages (Django: browse/feed_base.html and
 * page.html). Django renders an empty breadcrumb trail and the Back link above
 * the main wrapper.
 */
export function FeedPageShell({ backHref, error, children }: FeedPageShellProps) {
  return (
    <>
      <div className="govuk-width-container">
        <div className="govuk-breadcrumbs">
          <ol className="govuk-breadcrumbs__list" />
        </div>
        {backHref ? (
          <Link href={backHref} className="govuk-back-link">
            Back
          </Link>
        ) : null}
      </div>
      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          {error ? <ErrorSummary errors={[error]} /> : children}
        </div>
      </div>
    </>
  );
}
