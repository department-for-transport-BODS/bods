'use client';

import Link from 'next/link';
import { useParams, useSearchParams } from 'next/navigation';
import { useCallback } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faCaretDown, faCaretUp } from '@fortawesome/free-solid-svg-icons';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { ErrorDisplay } from '@/components/shared/ErrorDisplay';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { Pagination } from '@/components/shared/Pagination';
import { publishPath } from '@/config/client';
import { useApiResource } from '@/hooks/useApiResource';
import { api } from '@/lib/api-client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { LineHelpModal } from './LineHelpModal';
import './requires-attention.css';

export type RequiresAttentionKind = 'timetables' | 'fares';

interface RequiresAttentionResponse {
  ancestor: string;
  summary: {
    servicesRequiringAttention: number;
    totalInScopeInSeasonServices: number;
    percentage: number;
  };
  rows: { licenceNumber: string; serviceCode: string; lineNumber: string }[];
  pagination: { currentPage: number; totalPages: number };
  query: string;
  noResults: boolean;
  exportPath: string;
}

const KIND_CONFIG: Record<RequiresAttentionKind, { apiSegment: string; listSegment: string; defaultAncestor: string }> = {
  timetables: {
    apiSegment: 'timetables',
    listSegment: 'timetable',
    defaultAncestor: 'Review My Timetables Data',
  },
  fares: {
    apiSegment: 'fares',
    listSegment: 'fares',
    defaultAncestor: 'Review My Fares Data',
  },
};

const COLUMNS = [
  { field: 'licence_number', label: 'Licence number' },
  { field: 'service_code', label: 'Service code' },
  { field: 'line_number', label: 'Line', helpModal: true },
] as const;

type SortDirection = 'asc' | 'desc' | null;

function getSortDirection(sort: string, field: string): SortDirection {
  if (sort === field) return 'asc';
  if (sort === `-${field}`) return 'desc';
  return null;
}

/** Same cycle as django-tables2 `column.order_by_alias.next`. */
function sortHref(searchParams: URLSearchParams, field: string, direction: SortDirection): string {
  const params = new URLSearchParams(searchParams.toString());
  params.set('sort', direction === 'asc' ? `-${field}` : field);
  params.set('page', '1');
  return `?${params.toString()}`;
}

const SEARCH_ICON_PATH =
  'M776.594 331.75a9.418 9.418 0 0 0 2.428-6.296c0-5.213-4.268-9.454-9.51-9.454-5.244 0-9.512 4.242-9.512 9.454 0 5.213 4.268 9.455 9.51 9.455a9.523 9.523 0 0 0 5.04-1.444l4.176 4.152c.25.248.59.383.931.383.34 0 .681-.136.931-.383a1.295 1.295 0 0 0 .023-1.873l-4.017-3.994zm-13.939-6.296c0-3.746 3.065-6.814 6.855-6.814 3.792 0 6.833 3.068 6.833 6.814s-3.064 6.815-6.832 6.815-6.856-3.047-6.856-6.815z';

/**
 * "Service codes requiring attention" page shared by the timetable and fares
 * review journeys. Mirrors publish/requires_attention.html and
 * fares/requires_attention.html.
 */
export function RequiresAttentionContent({ kind }: { kind: RequiresAttentionKind }) {
  const config = KIND_CONFIG[kind];
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;
  const query = (searchParams.get('q') || '').trim();
  const sort = searchParams.get('sort') || '';
  const parsedPage = Number.parseInt(searchParams.get('page') || '1', 10);
  const page = Number.isNaN(parsedPage) || parsedPage < 1 ? 1 : parsedPage;

  const loadData = useCallback(() => {
    const requestParams = new URLSearchParams({ q: query, page: String(page) });
    if (sort) {
      requestParams.set('sort', sort);
    }
    return api.get<RequiresAttentionResponse>(
      `/api/publish/${config.apiSegment}/requires-attention/${encodeURIComponent(orgId)}/?${requestParams.toString()}`,
    );
  }, [config.apiSegment, orgId, query, page, sort]);

  const { data, isLoading, error } = useApiResource<RequiresAttentionResponse>(
    loadData,
    'Unable to load service codes requiring attention.',
  );

  const listPath = `/org/${orgId}/dataset/${config.listSegment}/`;
  const attentionPath = `${listPath}attention/`;

  return (
    <>
      <div className="govuk-width-container">
        <Breadcrumbs
          items={hostBreadcrumbs(
            'publish',
            { label: data?.ancestor ?? config.defaultAncestor, href: publishPath(listPath) },
            { label: 'Service Codes Requiring Attention', href: publishPath(attentionPath), current: true },
          )}
        />
      </div>

      <div className="app-masthead">
        <div className="govuk-width-container">
          <div className="govuk-grid-row govuk-!-margin-top-5">
            <div className="govuk-grid-column-two-thirds">
              <h1 className="govuk-heading-xl app-masthead__title">Service codes requiring attention</h1>
              <p className="govuk-body">
                The service codes listed here are registered with the OTC and are in scope of BODS, but are not yet
                published in a complete and accurate way.
              </p>
              <p className="govuk-body">
                Download the detailed export at the bottom of the page to determine the reason your service code is
                listed here.
              </p>
              <p className="govuk-body">Contact the service desk if you have any questions or require any support.</p>
            </div>
          </div>
        </div>
      </div>

      <div className="govuk-width-container">
        <div className="govuk-main-wrapper app-main-class">
          {isLoading && <LoadingSpinner message="Loading service codes requiring attention" />}
          {!isLoading && error && <ErrorDisplay type="server" message={error} />}

          {!isLoading && !error && data && (
            <>
              <div className="govuk-grid-column-full govuk-!-margin-bottom-9">
                <div className="govuk-grid-row">
                  <div className="govuk-grid-column-one-quarter">
                    <div className="feed-stat">
                      <span className="feed-stat__value">{data.summary.totalInScopeInSeasonServices}</span>
                      <span className="feed-stat__label govuk-!-font-size-16">
                        Total in scope/
                        <br />
                        in season registered services
                      </span>
                    </div>
                  </div>
                  <div className="govuk-grid-column-one-quarter">
                    <div className="feed-stat">
                      <span className="feed-stat__value">{data.summary.percentage}%</span>
                      <span className="feed-stat__label govuk-!-font-size-16 govuk-!-margin-bottom-2">
                        Services requiring
                        <br />
                        attention
                      </span>
                      {data.summary.percentage === 0 ? (
                        <span className="letter-spacing-0 govuk-tag--green govuk-tag">Compliant</span>
                      ) : (
                        <span className="letter-spacing-0 govuk-tag--red govuk-tag">Not Compliant</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>

              <div className="govuk-width-container">
                <div className="govuk-grid-row govuk-!-margin-top-0">
                  <form method="get">
                    <div className="govuk-grid-column-one-half">
                      <p id="search-description" className="govuk-body">
                        Search for a licence number, service code or line number
                      </p>
                      {/* Django's `.searchbox` has a 30px bottom margin */}
                      <div className="app-data-browser__searchbox govuk-!-margin-bottom-6">
                        <input
                          key={data.query}
                          className="app-data-browser__searchbox-input"
                          id="search"
                          name="q"
                          aria-labelledby="search-description"
                          type="search"
                          defaultValue={data.query}
                          placeholder=""
                        />
                        <button className="app-data-browser__searchbox-button" type="submit" aria-label="submit search">
                          <svg width="21" height="22" viewBox="0 0 21 22" xmlns="http://www.w3.org/2000/svg">
                            <g transform="translate(-760 -316)" fill="none" fillRule="evenodd">
                              <path d={SEARCH_ICON_PATH} fill="#FFF" fillRule="nonzero" />
                            </g>
                          </svg>
                        </button>
                      </div>
                    </div>
                  </form>

                  {data.noResults ? (
                    <div className="govuk-grid-column-two-thirds">
                      <h2 className="govuk-heading-m">Sorry, no results found for your search</h2>
                      <hr className="govuk-section-break govuk-section-break--xl govuk-section-break" />
                      <p className="govuk-body">
                        <b>Having trouble finding what you want?</b>
                      </p>
                      <ul className="govuk-list govuk-list--bullet">
                        <li>Check your spelling and try again</li>
                        <li>Use another search term</li>
                      </ul>
                    </div>
                  ) : (
                    <div className="govuk-width-container">
                      <div className="govuk-grid-column-full custom_govuk_table_border">
                        <div>
                          {/* Django compiles `.custom_govuk_table` with `@extend .govuk-table` */}
                          <table className="custom_govuk_table govuk-table">
                            <thead className="govuk-table__head">
                              <tr className="govuk-table__row">
                                {COLUMNS.map((column) => {
                                  const direction = getSortDirection(sort, column.field);
                                  return (
                                    <th
                                      key={column.field}
                                      aria-sort={
                                        direction === 'asc' ? 'ascending' : direction === 'desc' ? 'descending' : 'none'
                                      }
                                      role="columnheader"
                                      scope="col"
                                      className={`govuk-table__header orderable${direction ? ` ${direction}` : ''}`}
                                    >
                                      <Link
                                        className="column-header-link"
                                        role="button"
                                        href={sortHref(searchParams, column.field, direction)}
                                      >
                                        {column.label}
                                        <span className="hide-using-position">Sort your data by {column.label}</span>
                                      </Link>
                                      <FontAwesomeIcon icon={faCaretUp} className="order-up" />
                                      <FontAwesomeIcon icon={faCaretDown} className="order-down" />
                                      {'helpModal' in column && <LineHelpModal />}
                                    </th>
                                  );
                                })}
                              </tr>
                            </thead>
                            <tbody className="govuk-table__body">
                              {data.rows.map((row, index) => (
                                <tr
                                  key={`${row.serviceCode}-${row.lineNumber}-${index}`}
                                  className={`govuk-table__row ${index % 2 === 0 ? 'even' : 'odd'}`}
                                >
                                  <td className="govuk-table__cell">{row.licenceNumber}</td>
                                  <td className="govuk-table__cell">{row.serviceCode}</td>
                                  <td className="govuk-table__cell">{row.lineNumber}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                          <Pagination
                            currentPage={data.pagination.currentPage}
                            totalPages={data.pagination.totalPages}
                          />
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                <div className="govuk-grid-row govuk-!-margin-top-5">
                  <p className="govuk-body-s">Use the link below to download and view the entire list of service codes</p>
                  <p className="govuk-body-s">
                    <a className="govuk-link" href={publishPath(data.exportPath)}>
                      Download detailed export
                    </a>
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
}
