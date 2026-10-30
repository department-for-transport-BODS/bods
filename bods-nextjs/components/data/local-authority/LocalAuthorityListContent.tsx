'use client';

/**
 * Local Transport Authority profiles list (data host, `/local-authority/`)
 *
 * Source: transit_odp/browse/templates/browse/local_authority.html
 * View: transit_odp/browse/views/local_authority.py - LocalAuthorityView
 * API: transit_odp/browse/views/api.py - local_authority_list_api
 */

import Image from 'next/image';
import Link from 'next/link';
import { notFound, usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { BrowseSearchBanner } from '@/components/data/browser/BrowseSearchBanner';
import { DataBrowserResultCard } from '@/components/data/browser/DataBrowserResultCard';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { RangePagination } from '@/components/shared/RangePagination';
import { dataPath } from '@/config/client';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  DEFAULT_LTA_ORDERING,
  LOCAL_AUTHORITY_LIST_API_PATH,
  formatAuthIds,
  localAuthorityDetailUrl,
  type LocalAuthorityListResponse,
} from '@/lib/local-authority';

const ORDERING_OPTIONS = [
  { value: 'ui_lta_name_trimmed', label: 'Name A-Z' },
  { value: '-ui_lta_name_trimmed', label: 'Name Z-A' },
];

function LocalAuthorityListInner() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlQ = searchParams.get('q') ?? '';
  const urlOrdering = searchParams.get('ordering') ?? DEFAULT_LTA_ORDERING;
  const urlPage = searchParams.get('page') ?? '';

  const [searchValue, setSearchValue] = useState(urlQ);
  const [data, setData] = useState<LocalAuthorityListResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    setSearchValue(urlQ);
  }, [urlQ]);

  useEffect(() => {
    let cancelled = false;
    const query = new URLSearchParams();
    if (urlQ) query.set('q', urlQ);
    query.set('ordering', urlOrdering);
    if (urlPage) query.set('page', urlPage);

    setIsLoading(true);
    setError('');
    api
      .get<LocalAuthorityListResponse>(`${LOCAL_AUTHORITY_LIST_API_PATH}?${query.toString()}`)
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        // Django 404s for an out-of-range page; an unknown ordering has no Django page at all.
        if (err instanceof ApiError && (err.status === 404 || err.status === 400)) {
          setMissing(true);
          return;
        }
        setError('Failed to load local transport authorities');
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [urlOrdering, urlPage, urlQ]);

  if (missing) notFound();

  const navigate = (params: URLSearchParams) => {
    const queryString = params.toString();
    router.push(queryString ? `${pathname}?${queryString}` : pathname);
  };

  // Django submits the whole form, so a new search or sort always restarts at page 1.
  const submitSearch = (value?: string) => {
    const params = new URLSearchParams();
    const term = value ?? searchValue;
    if (term) params.set('q', term);
    params.set('ordering', urlOrdering);
    navigate(params);
  };

  const changeOrdering = (ordering: string) => {
    const params = new URLSearchParams();
    if (urlQ) params.set('q', urlQ);
    params.set('ordering', ordering);
    navigate(params);
  };

  // Django's `relative_url` puts the page first, then the other query params.
  const buildPageHref = (page: number) => {
    const params = new URLSearchParams(searchParams.toString());
    params.delete('page');
    const rest = params.toString();
    return `${pathname}?page=${page}${rest ? `&${rest}` : ''}`;
  };

  const count = data?.count ?? 0;

  return (
    <>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={hostBreadcrumbs('data', { label: 'Local Transport Authority Profiles', href: dataPath('/local-authority') })}
        />
      </div>

      <BrowseSearchBanner
        title="Local Transport Authority"
        description="Search for a specific Local Transport Authority"
        placeholder="Enter Local Transport Authority name"
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onSearchSubmit={submitSearch}
        suggestions={data?.names}
      />

      <div className="govuk-width-container">
        <div className="govuk-grid-row govuk-!-margin-top-5">
          <div className="govuk-grid-column-two-thirds">
            {error && <ErrorDisplay message={error} />}
            {isLoading && !data ? (
              <LoadingSpinner message="Loading local transport authorities" />
            ) : (
              data && (
                <>
                  <div className="app-data-browser__results-heading">
                    {count > 1 && <span className="govuk-body">{count} results</span>}
                    {count === 1 && <span className="govuk-body">1 result</span>}
                    {count === 0 && (
                      <h3 className="govuk-heading-m">Sorry, no results found{data.q ? ` for ${data.q}` : ''}</h3>
                    )}
                  </div>
                  <div className="app-data-browser__filter-pillbox">
                    {data.q && (
                      <>
                        <span className="govuk-label govuk-!-font-weight-bold govuk-!-padding-right-3">Containing</span>
                        <Link href={`${pathname}?ordering=${encodeURIComponent(data.ordering)}`}>
                          <span className="app-data-browser__filter-pill">
                            <Image src="/assets/images/icon-cross.png" alt="delete-icon" width={18} height={19} />
                            {data.q}
                          </span>
                        </Link>
                      </>
                    )}
                  </div>
                  <div className="app-data-browser__sort-control govuk-form-group">
                    <label className="govuk-label" htmlFor="ordering">
                      Sort by
                    </label>
                    <select
                      className="govuk-select"
                      id="ordering"
                      name="ordering"
                      aria-label="Sort by"
                      value={data.ordering}
                      onChange={(event) => changeOrdering(event.target.value)}
                    >
                      {ORDERING_OPTIONS.map((option) => (
                        <option key={option.value} value={option.value}>
                          {option.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="govuk-body">
                    {data.results.length === 0 ? (
                      <div>
                        <hr className="govuk-section-break govuk-section-break--m" />
                        <h4 className="govuk-heading-s">Having trouble finding what you want?</h4>
                        <ul className="govuk-list govuk-list--bullet">
                          <li>Check your spelling and try again</li>
                        </ul>
                      </div>
                    ) : (
                      data.results.map((lta, index) => (
                        <div className="app-data-browser__result-item" key={lta.name}>
                          {index > 0 && <hr className="app-data-browser__result-divider" />}
                          <DataBrowserResultCard
                            title={lta.name}
                            href={localAuthorityDetailUrl(formatAuthIds(lta.authIds))}
                            keyValues={[
                              {
                                key: 'Services requiring attention:',
                                value: `${lta.servicesRequireAttentionPercentage} %`,
                              },
                            ]}
                          />
                        </div>
                      ))
                    )}
                  </div>
                  {count > 0 && (
                    <>
                      <hr className="govuk-section-break govuk-section-break--m govuk-section-break--visible" />
                      <RangePagination
                        currentPage={data.page}
                        numPages={data.numPages}
                        pageRange={data.pageRange}
                        buildHref={buildPageHref}
                      />
                    </>
                  )}
                </>
              )
            )}
          </div>
        </div>
      </div>
    </>
  );
}

export function LocalAuthorityListContent() {
  return (
    <Suspense fallback={null}>
      <LocalAuthorityListInner />
    </Suspense>
  );
}
