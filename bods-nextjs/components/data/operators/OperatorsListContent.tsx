'use client';

/**
 * Operator Profiles list (data host, `/operators/`)
 *
 * Source: transit_odp/browse/templates/browse/operators.html
 * View: transit_odp/browse/views/operators.py - OperatorsView
 * API: transit_odp/browse/views/operators_api.py - operators_list_api
 */

import { notFound, usePathname, useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import { BrowseSearchBanner } from '@/components/data/browser/BrowseSearchBanner';
import { DataBrowserResultCard } from '@/components/data/browser/DataBrowserResultCard';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { RangePagination } from '@/components/shared/RangePagination';
import { SearchSummaryBar } from '@/components/data/browser/SearchSummaryBar';
import { ApiError, api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import {
  formatOperatorDate,
  operatorDetailUrl,
  operatorsApiPath,
  type OperatorListResponse,
} from '@/lib/operators';

const DEFAULT_ORDERING = 'name';

const ORDERING_OPTIONS = [
  { value: 'name', label: 'Name A-Z' },
  { value: '-name', label: 'Name Z-A' },
  { value: '-created', label: 'Date registered newest' },
  { value: 'created', label: 'Date registered oldest' },
];

function OperatorsListInner() {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const urlQ = searchParams.get('q') ?? '';
  const urlOrdering = searchParams.get('ordering') ?? DEFAULT_ORDERING;
  const urlPage = searchParams.get('page') ?? '';

  const [searchValue, setSearchValue] = useState(urlQ);
  const [data, setData] = useState<OperatorListResponse | null>(null);
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
      .get<OperatorListResponse>(operatorsApiPath(query))
      .then((response) => {
        if (!cancelled) setData(response);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        if (err instanceof ApiError && err.status === 404) {
          setMissing(true);
          return;
        }
        setError('Failed to load operators');
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
          items={hostBreadcrumbs('data', { label: 'Operator Profiles', href: pathname, current: true })}
        />
      </div>

      <BrowseSearchBanner
        title="Operator Profiles"
        description="Search for a specific operator"
        placeholder="Enter operator name"
        searchValue={searchValue}
        onSearchChange={setSearchValue}
        onSearchSubmit={submitSearch}
        suggestions={data?.operatorNames}
      />

      <div className="govuk-width-container">
        <div className="govuk-grid-row govuk-!-margin-top-5">
          <div className="govuk-grid-column-two-thirds">
            {error && <ErrorDisplay message={error} />}
            {isLoading && !data ? (
              <LoadingSpinner message="Loading operators" />
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
                  <SearchSummaryBar
                    searchTerm={data.q}
                    clearSearchHref={`${pathname}?ordering=${encodeURIComponent(data.ordering)}`}
                    showContaining
                    removeSectionBreakTopMargin
                  />
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
                      data.results.map((operator, index) => (
                        <div className="app-data-browser__result-item" key={operator.id}>
                          {index > 0 && <hr className="app-data-browser__result-divider" />}
                          <DataBrowserResultCard
                            title={operator.name}
                            href={operatorDetailUrl(operator.id)}
                            keyValues={[{ key: 'Date registered:', value: formatOperatorDate(operator.created) }]}
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

export function OperatorsListContent() {
  return (
    <Suspense fallback={null}>
      <OperatorsListInner />
    </Suspense>
  );
}
