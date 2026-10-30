'use client';

import { useCallback, type ReactNode } from 'react';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { dataPath, wwwPath } from '@/config/client';
import { useApiResource } from '@/hooks/useApiResource';
import { api } from '@/lib/api-client';
import { dataApiPath } from '@/lib/api-paths';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';

interface DownloadPageProps<T> {
  title: string;
  /** Last breadcrumb label and its public data-host path. */
  breadcrumb: { label: string; path: string };
  /** Django `/api/...` path of the JSON endpoint that backs the page. */
  endpoint: string;
  /** Django's `inner` block renders an empty spaced row on the avl/fares/disruptions pages. */
  withTrailingRow?: boolean;
  children: (data: T) => ReactNode;
}

/**
 * Shared frame for the data-host "download" pages.
 *
 * Source: transit_odp/browse/templates/browse/base.html (heading + secondary
 * column layout), browse/snippets/download_secondary_links.html and the
 * breadcrumbs of each download_*.html template.
 */
export function DownloadPage<T>({
  title,
  breadcrumb,
  endpoint,
  withTrailingRow = false,
  children,
}: DownloadPageProps<T>) {
  const fetchPage = useCallback(() => api.get<T>(dataApiPath(endpoint)), [endpoint]);
  const { data, isLoading, error } = useApiResource<T>(fetchPage, 'Failed to load download options');

  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs(
          'data',
          { label: 'Download All Data', href: dataPath('/downloads') },
          { label: breadcrumb.label, href: dataPath(breadcrumb.path) },
        )}
      />

      <div className="govuk-main-wrapper app-main-class">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl dont-break-out" aria-label="Heading Title">
              {title}
            </h1>
            {isLoading && <LoadingSpinner message="Loading" />}
            {!isLoading && error && <ErrorDisplay type="server" message={error} />}
            {!isLoading && !error && data && children(data)}
          </div>
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">Need further help?</h2>
            <ul className="govuk-list">
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={dataPath('/guide-me')}>
                  Guide me
                </Link>
              </li>
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={wwwPath('/changelog')}>
                  Service changelog
                </Link>
              </li>
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={wwwPath('/contact')}>
                  Contact us for technical issues
                </Link>
              </li>
            </ul>
          </div>
        </div>
        {withTrailingRow && <div className="govuk-grid-row govuk-!-margin-top-9" />}
      </div>
    </div>
  );
}
